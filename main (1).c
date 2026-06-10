#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_WORDS 200

// 데이터 구조: 구조체(Structure) 사용
typedef struct {
    char word[50];
    char meaning[100];
} Vocabulary;

// 모듈화: 4개 이상의 사용자 정의 함수 구현
void clearInputBuffer();
int loadWordsFromFile(const char* filename, Vocabulary list[]);
void addWordToFile(const char* filename, const char* word, const char* meaning);
void deleteWordFromFile(const char* filename, const char* word);
void updateWordInFile(const char* filename, const char* word, const char* new_meaning);

int main(int argc, char* argv[]) {
    // 예외 처리: 인자 개수가 부족하게 들어온 경우 방어
    if (argc < 3) {
        printf("ERROR: Missing arguments.\n");
        return 1;
    }

    char* action = argv[1];
    char* filename = argv[2];

    if (strcmp(action, "add") == 0 && argc == 5) {
        addWordToFile(filename, argv[3], argv[4]);
    }
    else if (strcmp(action, "delete") == 0 && argc == 4) {
        deleteWordFromFile(filename, argv[3]);
    }
    else if (strcmp(action, "update") == 0 && argc == 5) {
        updateWordInFile(filename, argv[3], argv[4]);
    } 
    else {
        printf("ERROR: Invalid Action Command.\n");
        return 1;
    }

    return 0;
}

// 함수 1: 입력 버퍼를 비워 문자가 입력되었을 때 무한 루프를 방지하는 방어 코드
void clearInputBuffer() {
    while (getchar() != '\n');
}

// 함수 2: 파일 입출력을 통해 데이터를 불러오는 함수
int loadWordsFromFile(const char* filename, Vocabulary list[]) {
    FILE* file = fopen(filename, "r");
    if (file == NULL) return 0;

    char line[250];
    int count = 0;

    if (fgets(line, sizeof(line), file) == NULL) { // 헤더 skip 예외 처리
        fclose(file);
        return 0;
    }

    while (fgets(line, sizeof(line), file) && count < MAX_WORDS) {
        line[strcspn(line, "\n")] = 0; 
        char* token = strtok(line, ",");
        if (token) {
            strcpy(list[count].word, token);
            token = strtok(NULL, ",");
            if (token) {
                strcpy(list[count].meaning, token);
                count++;
            }
        }
    }
    fclose(file);
    return count;
}

// 함수 3: 단어 추가 로직
void addWordToFile(const char* filename, const char* word, const char* meaning) {
    int is_new = 0;
    FILE* check = fopen(filename, "r");
    if (check == NULL) is_new = 1;
    else fclose(check);

    FILE* file = fopen(filename, "a");
    if (file == NULL) return;

    if (is_new) {
        fprintf(file, "Word,Meaning\n"); // 파일 입출력: csv 헤더 생성
    }
    fprintf(file, "%s,%s\n", word, meaning);
    fclose(file);
    printf("SUCCESS\n");
}

// 함수 4: 특정 단어 삭제 로직
void deleteWordFromFile(const char* filename, const char* word) {
    Vocabulary list[MAX_WORDS];
    int count = loadWordsFromFile(filename, list);

    FILE* file = fopen(filename, "w");
    if (file == NULL) return;

    fprintf(file, "Word,Meaning\n");
    for (int i = 0; i < count; i++) {
        if (strcmp(list[i].word, word) != 0) {
            fprintf(file, "%s,%s\n", list[i].word, list[i].meaning);
        }
    }
    fclose(file);
    printf("SUCCESS\n");
}

// 함수 5: 특정 단어 뜻 수정 로직
void updateWordInFile(const char* filename, const char* word, const char* new_meaning) {
    Vocabulary list[MAX_WORDS];
    int count = loadWordsFromFile(filename, list);

    FILE* file = fopen(filename, "w");
    if (file == NULL) return;

    fprintf(file, "Word,Meaning\n");
    for (int i = 0; i < count; i++) {
        if (strcmp(list[i].word, word) == 0) {
            strcpy(list[i].meaning, new_meaning);
        }
        fprintf(file, "%s,%s\n", list[i].word, list[i].meaning);
    }
    fclose(file);
    printf("SUCCESS\n");
}
