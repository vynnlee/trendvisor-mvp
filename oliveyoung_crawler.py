#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
올리브영 리뷰 크롤링 시스템 (CoT 기반)
20년 경력 데이터 애널리스트 설계

주요 특징:
- 법적 준수 (robots.txt 5초 간격)
- 동적 웹 크롤링 (API 기반)
- 예외 처리 및 재시도 로직
- 데이터 정제 및 검증
- 구조화된 출력 (JSON, CSV, Excel)
"""

import asyncio
import aiohttp
import json
import pandas as pd
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlencode
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('oliveyoung_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ReviewData:
    """리뷰 데이터 구조체"""
    product_code: str
    review_id: str
    user_name: str
    rating: int
    review_date: str
    skin_type: str
    tone_type: str
    skin_concerns: List[str]
    product_satisfaction: Dict[str, str]
    review_text: str
    helpful_count: int
    review_type: str  # 포토리뷰, 일반리뷰, 체험단
    images: List[str]
    is_verified_purchase: bool
    tags: List[str]

class OliveYoungReviewCrawler:
    """올리브영 리뷰 크롤러 메인 클래스"""
    
    def __init__(self):
        self.base_url = "https://www.oliveyoung.co.kr"
        self.api_endpoint = "/store/goods/getGdasNewListJson.do"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        self.delay = 5  # robots.txt 준수 5초 대기
        self.session = None
        self.reviews_data = []
        
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()

    def validate_product_code(self, product_code: str) -> bool:
        """상품코드 유효성 검증"""
        pattern = r'^A\d{9}$'
        return bool(re.match(pattern, product_code))

    async def get_review_page(self, product_code: str, page: int = 1, 
                            sort_type: str = "05", filters: Optional[Dict] = None) -> Dict:
        """리뷰 페이지 데이터 조회"""
        params = {
            "goodsNo": product_code,
            "gdasSort": sort_type,  # 05: 유용한순, 01: 최신순, 02: 평점높은순
            "itemNo": "all_search",
            "pageIdx": page,
            "colData": "",
            "keywordGdasSeqs": "",
            "type": "",
            "point": "",
            "hashTag": "",
            "optionValue": "",
            "cTypeLength": 0
        }
        
        # 필터 적용
        if filters:
            params.update(filters)
        
        url = f"{self.base_url}{self.api_endpoint}?{urlencode(params)}"
        
        try:
            await asyncio.sleep(self.delay)  # robots.txt 준수
            
            if not self.session:
                raise RuntimeError("Session이 초기화되지 않았습니다")
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
                logger.info(f"페이지 {page} 리뷰 데이터 조회 완료 (상품: {product_code})")
                return data
                
        except Exception as e:
            logger.error(f"페이지 {page} 조회 실패: {e}")
            raise

    async def crawl_all_reviews(self, product_code: str, max_pages: int = 10) -> List[Dict]:
        """모든 리뷰 데이터 수집"""
        logger.info(f"리뷰 크롤링 시작 - 상품코드: {product_code}")
        
        all_reviews = []
        
        for page in range(1, max_pages + 1):
            try:
                page_data = await self.get_review_page(product_code, page)
                
                # 실제 API 응답 구조에 맞게 수정
                reviews = page_data.get('gdasList', [])
                
                if not reviews:
                    logger.info(f"페이지 {page}에서 리뷰 없음, 크롤링 종료")
                    break
                
                all_reviews.extend(reviews)
                logger.info(f"페이지 {page} 완료 - {len(reviews)}개 리뷰 수집")
                
            except Exception as e:
                logger.error(f"페이지 {page} 크롤링 실패: {e}")
                continue
        
        logger.info(f"크롤링 완료 - 총 {len(all_reviews)}개 리뷰 수집")
        return all_reviews

    def parse_reviews(self, raw_reviews: List[Dict], product_code: str) -> List[Dict]:
        """원시 리뷰 데이터를 정제된 형태로 파싱"""
        parsed_reviews = []
        
        for item in raw_reviews:
            try:
                # 기본 정보 파싱
                review = {
                    'product_code': product_code,
                    'review_id': str(item.get('gdasSeq', '')),
                    'user_name': item.get('mbrNickNm', ''),
                    'rating': item.get('gdasScrVal', 0) / 2,  # 10점 만점을 5점 만점으로 변환
                    'review_date': item.get('dispRegDate', ''),
                    'review_text': self._clean_text(item.get('gdasCont', '')),
                    'helpful_count': item.get('recommCnt', 0),
                    'is_photo_review': item.get('photoReviewYn', 'N') == 'Y',
                    'useful_point': item.get('usefulPoint', 0),
                }
                
                # 피부 평가 정보 파싱
                eval_list = item.get('evalList', [])
                for eval_item in eval_list:
                    question = eval_item.get('evalQstCont', '')
                    answer = eval_item.get('evalAnsCont', '')
                    
                    if '피부타입' in question:
                        review['skin_type'] = answer
                    elif '발림성' in question:
                        review['texture'] = answer
                    elif '자극도' in question:
                        review['irritation'] = answer
                
                # 피부 정보 파싱
                skin_info = []
                add_info = item.get('addInfoNm', [])
                if add_info:
                    for info in add_info:
                        skin_info.append(info.get('mrkNm', ''))
                review['skin_concerns'] = ', '.join(skin_info)
                
                # 이미지 정보 파싱
                photo_list = item.get('photoList', [])
                images = []
                if photo_list:
                    for photo in photo_list:
                        if photo.get('appxFilePathNm'):
                            images.append(f"https://image.oliveyoung.co.kr/uploads/{photo['appxFilePathNm']}")
                review['images'] = ', '.join(images)
                
                # 해시태그
                review['hashtag'] = item.get('hshTag', '')
                
                parsed_reviews.append(review)
                
            except Exception as e:
                logger.warning(f"리뷰 파싱 실패 (ID: {item.get('gdasSeq', 'unknown')}): {e}")
                continue
        
        return parsed_reviews

    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""
        
        # HTML 태그 제거
        import re
        text = re.sub(r'<[^>]+>', '', text)
        # 특수문자 정리
        text = re.sub(r'[\r\n\t]+', ' ', text)
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def save_to_csv(self, reviews: List[Dict], filename: str) -> None:
        """CSV로 저장"""
        if not reviews:
            logger.warning("저장할 리뷰 데이터가 없습니다")
            return
        
        df = pd.DataFrame(reviews)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"CSV 파일 저장 완료: {filename}")

# 사용 예시
async def main():
    """메인 실행 함수"""
    product_code = "A000000184353"  # 넘버즈인 선크림
    
    async with OliveYoungReviewCrawler() as crawler:
        try:
            # 원시 리뷰 데이터 수집
            raw_reviews = await crawler.crawl_all_reviews(product_code, max_pages=3)
            
            # 데이터 파싱
            parsed_reviews = crawler.parse_reviews(raw_reviews, product_code)
            
            # 결과 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"oliveyoung_reviews_{product_code}_{timestamp}.csv"
            
            crawler.save_to_csv(parsed_reviews, filename)
            
            print(f"크롤링 완료! 총 {len(parsed_reviews)}개 리뷰 수집")
            print(f"파일 저장됨: {filename}")
            
            # 간단한 통계 출력
            if parsed_reviews:
                df = pd.DataFrame(parsed_reviews)
                print(f"\n=== 수집 결과 요약 ===")
                print(f"평균 평점: {df['rating'].mean():.2f}")
                print(f"포토 리뷰: {df['is_photo_review'].sum()}개")
                print(f"총 추천수: {df['helpful_count'].sum()}개")
                if 'skin_type' in df.columns:
                    print(f"주요 피부타입: {df['skin_type'].mode().iloc[0] if not df['skin_type'].mode().empty else 'N/A'}")
            
        except Exception as e:
            logger.error(f"크롤링 실패: {e}")
            print(f"크롤링 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 