from flask import Flask, render_template_string, request, redirect, url_for
import pandas as pd
import os
import subprocess
import glob
import matplotlib
matplotlib.use('Agg') # GUI 없는 환경(Replit)에서 그래프 저장을 위한 설정
import matplotlib.pyplot as plt
from wordcloud import WordCloud

app = Flask(__name__)
C_ENGINE = "./main"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 하이브리드 스마트 단어장</title>
    <style>
        body { font-family: 'Arial', sans-serif; background: #f8f9fa; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { max-width: 900px; width: 100%; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        h1, h2, h3 { color: #2c3e50; text-align: center; }
        .set-selector, .word-form { background: #f1f3f5; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
        select, input, button { padding: 10px; margin: 5px; font-size: 1rem; border-radius: 5px; border: 1px solid #ced4da; }
        button { background: #4dabf7; color: white; border: none; cursor: pointer; font-weight: bold; }
        button.del-btn { background: #ff6b6b; }
        button.edit-btn { background: #fcc419; }
        .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }
        .card { height: 130px; perspective: 1000px; cursor: pointer; }
        .card-inner { width: 100%; height: 100%; text-align: center; transition: transform 0.5s; transform-style: preserve-3d; position: relative; }
        .card.flipped .card-inner { transform: rotateY(180deg); }
        .card-front, .card-back { position: absolute; width: 100%; height: 100%; backface-visibility: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05); padding: 10px; box-sizing: border-box; }
        .card-front { background: #495057; font-size: 1.3rem; font-weight: bold; }
        .card-back { background: #2b8a3e; transform: rotateY(180deg); font-size: 1.1rem; }
        .action-layer { margin-top: 8px; }
        .visual-section { display: flex; flex-direction: column; align-items: center; gap: 20px; margin-top: 40px; border-top: 2px dashed #dee2e6; padding-top: 20px; }
        .visual-section img { max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
<div class="container">
    <h1>🚀 AI 하이브리드 멀티 단어장 패키지</h1>

    <div class="set-selector">
        <form action="/" method="GET">
            <label>📂 단어장 카테고리 선택: </label>
            <select name="set_name" onchange="this.form.submit()">
                {% for s in all_sets %}
                <option value="{{ s }}" {% if s == current_set %}selected{% endif %}>{{ s }}</option>
                {% endfor %}
            </select>
        </form>
        <form action="/create-set" method="POST" style="margin-top: 10px;">
            <input type="text" name="new_set" placeholder="새 단어장 세트 이름 (예: 수능영어)" required>
            <button type="submit">카테고리 생성</button>
        </form>
    </div>

    <div class="word-form">
        <h3>➕ '{{ current_set }}' 단어장에 추가</h3>
        <form action="/add" method="POST">
            <input type="hidden" name="set_name" value="{{ current_set }}">
            <input type="text" name="word" placeholder="영어 단어" required>
            <input type="text" name="meaning" placeholder="한국어 뜻" required>
            <button type="submit">C 엔진에 등록</button>
        </form>
    </div>

    <h2>🃏 플래시카드 학습 스크린 (클릭 시 뒤집힘)</h2>
    <div class="card-grid">
        {% for row in vocab_list %}
        <div class="card" onclick="this.classList.toggle('flipped')">
            <div class="card-inner">
                <div class="card-front">
                    <div>{{ row['Word'] }}</div>
                </div>
                <div class="card-back">
                    <div>{{ row['Meaning'] }}</div>
                    <div class="action-layer">
                        <button class="edit-btn" onclick="event.stopPropagation(); editWord('{{ row['Word'] }}')">수정</button>
                        <button class="del-btn" onclick="event.stopPropagation(); location.href='/delete?set_name={{ current_set }}&word={{ row['Word'] }}'">삭제</button>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="visual-section">
        <h2>📊 파이썬 특화 분석 리포트 (Matplotlib & WordCloud)</h2>
        {% if vocab_list|length > 0 %}
            <div><strong>현재 단어장에 등록된 총 단어 수:</strong> {{ vocab_list|length }}개</div>
            <img src="/static/chart.png?v={{ version }}" alt="단어 통계 차트">
            <img src="/static/wordcloud.png?v={{ version }}" alt="단어 워드클라우드">
        {% else %}
            <p>시각화 데이터가 부족합니다. 단어를 먼저 등록해 주세요!</p>
        {% endif %}
    </div>
</div>

<script>
function editWord(word) {
    var res = prompt(word + "의 수정할 뜻을 입력하세요:");
    if(res) {
        location.href = "/update?set_name={{ current_set }}&word=" + word + "&meaning=" + res;
    }
}
</script>
</body>
</html>
"""

# 파이썬 시각화 및 라이브러리 활용 함수
def generate_reports(filename):
    if not os.path.exists(filename):
        return
    try:
        # Pandas로 C언어가 저장한 파일 읽기
        df = pd.read_csv(filename)
        if df.empty or len(df) == 0:
            return

        os.makedirs('static', exist_ok=True)

        # 1. Matplotlib 시각화: 글자 길이 분포 막대 그래프 생성
        df['Length'] = df['Word'].apply(lambda x: len(str(x)))
        plt.figure(figsize=(6, 3.5))
        plt.bar(df['Word'].astype(str), df['Length'], color='#4dabf7')
        plt.title('Word Length Analysis', fontsize=12, fontweight='bold')
        plt.xlabel('Words')
        plt.ylabel('Letter Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig('static/chart.png', dpi=150)
        plt.close()

        # 2. Python 라이브러리 활용: 등록된 영어 단어로 WordCloud 생성
        text = " ".join(df['Word'].astype(str).tolist())
        wordcloud = WordCloud(width=600, height=350, background_color='white', colormap='plasma').generate(text)
        wordcloud.to_file('static/wordcloud.png')
    except Exception as e:
        print(f"시각화 생성 중 오류 발생: {e}")

def get_all_sets():
    files = glob.glob("voca_*.csv")
    sets = [f.replace("voca_", "").replace(".csv", "") for f in files]
    return sets if sets else ["기본단어장"]

@app.route('/')
def home():
    all_sets = get_all_sets()
    current_set = request.args.get('set_name', all_sets[0])

    filename = f"voca_{current_set}.csv"
    vocab_list = []

    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            vocab_list = df.to_dict(orient='records')
        except:
            vocab_list = []

    # 웹 로드 시 시각화 파일 실시간 갱신
    generate_reports(filename)
    import time
    version = int(time.time()) # 브라우저 이미지 캐시 방지용 변수

    return render_template_string(HTML_TEMPLATE, all_sets=all_sets, current_set=current_set, vocab_list=vocab_list, version=version)

@app.route('/create-set', methods=['POST'])
def create_set():
    new_set = request.form.get('new_set')
    filename = f"voca_{new_set}.csv"
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write("Word,Meaning\n")
    return redirect(url_for('home', set_name=new_set))

@app.route('/add', methods=['POST'])
def add():
    set_name = request.form.get('set_name')
    word = request.form.get('word')
    meaning = request.form.get('meaning')
    subprocess.run([C_ENGINE, "add", f"voca_{set_name}.csv", word, meaning])
    return redirect(url_for('home', set_name=set_name))

@app.route('/delete')
def delete():
    set_name = request.args.get('set_name')
    word = request.args.get('word')
    subprocess.run([C_ENGINE, "delete", f"voca_{set_name}.csv", word])
    return redirect(url_for('home', set_name=set_name))

@app.route('/update')
def update():
    set_name = request.args.get('set_name')
    word = request.args.get('word')
    meaning = request.args.get('meaning')
    subprocess.run([C_ENGINE, "update", f"voca_{set_name}.csv", word, meaning])
    return redirect(url_for('home', set_name=set_name))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
