#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
올리브영 API 응답 구조 테스트 스크립트
실제 API 응답을 확인하여 파싱 로직을 검증합니다.
"""

import asyncio
import aiohttp
import json
from urllib.parse import urlencode

async def test_oliveyoung_api():
    """올리브영 리뷰 API 테스트"""
    
    # API 설정
    base_url = "https://www.oliveyoung.co.kr"
    api_endpoint = "/store/goods/getGdasNewListJson.do"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do",
    }
    
    # 테스트 파라미터
    params = {
        "goodsNo": "A000000184353",  # 넘버즈인 선크림
        "gdasSort": "05",  # 유용한순
        "itemNo": "all_search",
        "pageIdx": 1,
        "colData": "",
        "keywordGdasSeqs": "",
        "type": "",
        "point": "",
        "hashTag": "",
        "optionValue": "",
        "cTypeLength": 0
    }
    
    url = f"{base_url}{api_endpoint}?{urlencode(params)}"
    
    print(f"🔍 API 테스트 시작...")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                print(f"\n📡 응답 상태: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # 응답 구조 분석
                    print(f"\n📊 응답 데이터 구조:")
                    print(f"데이터 타입: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"최상위 키들: {list(data.keys())}")
                        
                        # 주요 데이터 확인
                        for key, value in data.items():
                            print(f"\n🔑 {key}:")
                            print(f"  타입: {type(value)}")
                            
                            if isinstance(value, dict):
                                print(f"  하위 키들: {list(value.keys())}")
                                
                                # gdasList나 reviewList 같은 배열 찾기
                                for sub_key, sub_value in value.items():
                                    if isinstance(sub_value, list) and sub_value:
                                        print(f"\n  📋 {sub_key} (리스트, {len(sub_value)}개 항목):")
                                        
                                        # 첫 번째 아이템 구조 확인
                                        if sub_value:
                                            first_item = sub_value[0]
                                            if isinstance(first_item, dict):
                                                print(f"    첫 번째 아이템 키들: {list(first_item.keys())}")
                                                
                                                # 주요 필드들 출력
                                                important_fields = [
                                                    'gdasSeq', 'mbrId', 'gdasPnt', 'rgstDttm',
                                                    'gdasCont', 'recomCnt', 'skinType', 'toneType'
                                                ]
                                                
                                                for field in important_fields:
                                                    if field in first_item:
                                                        print(f"    {field}: {first_item[field]}")
                            
                            elif isinstance(value, list) and value:
                                print(f"  리스트 길이: {len(value)}")
                                if isinstance(value[0], dict):
                                    print(f"  첫 번째 아이템 키들: {list(value[0].keys())}")
                    
                    # 전체 응답을 파일로 저장
                    with open('api_response_sample.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"\n💾 전체 응답이 'api_response_sample.json'에 저장되었습니다.")
                    
                else:
                    print(f"❌ 응답 실패: {response.status}")
                    text = await response.text()
                    print(f"응답 내용: {text[:500]}...")
                    
        except aiohttp.ClientError as e:
            print(f"❌ 네트워크 오류: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 오류: {e}")
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_oliveyoung_api()) 