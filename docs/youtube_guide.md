공유해주신 문제점(API 검색 정확도 저하)과 해결 방안을 중심으로, 파이썬 예제 코드를 포함한 가이드 문서를 작성했습니다. 아래의 내용을 복사하여 `.md` 파일이나 `.txt` 파일로 저장해 활용하시기 바랍니다.

---

## 📄 YouTube 공식 MV 검색 도구 최적화 가이드

본 문서는 Python과 YouTube Data API v3를 활용하여 검색 결과의 정확도를 높이고, 공식 뮤직비디오(Official MV) 링크만을 추출하기 위한 기술적 접근법을 정리한 문서입니다.

### 1. 검색 정확도 저하의 원인
* **검색어 모호성:** 커버 영상, 가사(Lyrics) 영상, 교차 편집 영상이 상단에 노출됨.
* **API 기본 정렬:** 관련성(Relevance) 기준 정렬 시 조회수가 높은 팬 메이드 영상이 우선될 수 있음.
* **채널 검증 부재:** 공식 아티스트 채널과 일반 채널의 구분이 코드상에서 이루어지지 않음.

### 2. 정확도 향상을 위한 전략
1.  **쿼리 고도화:** `"{Artist}" "{Title}"` 처럼 큰따옴표를 사용하여 정확한 키워드 매칭을 유도하고, `-cover`, `-lyrics` 등의 제외 키워드 활용.
2.  **채널 검증:** 검색된 영상의 업로더 채널 이름에 'Official', 'VEVO' 또는 기획사 이름이 포함되어 있는지 확인.
3.  **영상 길이 필터링:** MV는 대개 3~5분 사이이므로 1분 미만(티저/쇼츠)이나 10분 이상(모음집) 제외.
4.  **카테고리 필터링:** 카테고리 ID `10`(Music) 영상만 필터링.

---

### 3. Python 예제 소스 코드 (API v3 활용)

```python
from googleapiclient.discovery import build
import re

# API 설정
API_KEY = "YOUR_API_KEY"  # 실제 API 키로 변경하세요.
youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_official_mv(artist, title):
    # 1. 쿼리 고도화 (정확한 매칭 및 불필요 키워드 제외)
    search_query = f'"{artist}" "{title}" official mv -cover -lyrics -reaction'
    
    try:
        # 검색 요청
        search_response = youtube.search().list(
            q=search_query,
            part='snippet',
            maxResults=5,
            type='video',
            videoCategoryId='10'  # 음악 카테고리로 제한
        ).execute()

        for item in search_response['items']:
            video_title = item['snippet']['title'].lower()
            channel_title = item['snippet']['channelTitle'].lower()
            video_id = item['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # 2. 공식 채널 및 제목 검증 로직
            # 채널명에 가수 이름이나 'Official', 'VEVO', 'Labels' 등이 있는지 확인
            is_official_channel = any(word in channel_title for word in [artist.lower(), 'official', 'vevo', 'labels'])
            
            # 제목에 'official' 문구가 포함되어 있는지 확인 (티저 제외)
            is_official_video = 'official' in video_title and 'teaser' not in video_title

            if is_official_channel or is_official_video:
                return {
                    "status": "success",
                    "title": item['snippet']['title'],
                    "url": video_url,
                    "channel": item['snippet']['channelTitle']
                }

    except Exception as e:
        return {"status": "error", "message": str(e)}

    return {"status": "fail", "message": "공식 뮤직비디오를 찾을 수 없습니다."}

# 사용 예시
result = get_official_mv("NewJeans", "Hype Boy")
if result['status'] == 'success':
    print(f"곡 제목: {result['title']}")
    print(f"채널명: {result['channel']}")
    print(f"링크: {result['url']}")
else:
    print(result['message'])
```

---

### 4. 추가 팁
* **Region Code:** 한국 곡을 주로 찾으신다면 API 호출 시 `regionCode='KR'` 파라미터를 추가하세요.
* **정규 표현식:** 가수 이름이 영어/한글 혼용될 경우 정규식을 통해 제목 내 포함 여부를 더 엄격하게 체크할 수 있습니다.

---
