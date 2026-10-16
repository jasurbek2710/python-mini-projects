
import requests
import json
import time
from pathlib import Path
from datetime import datetime


def get_baidu_poi(roi_key, city_str, baidu_ak, output):
    """
    Получает POI (точки интереса) из Baidu Maps API.

    roi_key: название объекта для поиска
    city_str: название города
    baidu_ak: ключ Baidu Maps API
    output: путь к папке для сохранения файлов
    """

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    now_time = datetime.now().strftime("%Y-%m-%d")
    txt_path = output_dir / f"{now_time}.txt"
    log_path = output_dir / f"{now_time}.log"

    page_num = 0
    base_url = "https://api.map.baidu.com/place/v2/search"

    params = {
        "query": roi_key,
        "region": city_str,
        "output": "json",
        "ak": baidu_ak,
        "scope": 2,
        "page_size": 20,
    }

    with requests.Session() as session:
        while True:
            params["page_num"] = page_num

            try:
                response = session.get(
                    base_url,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                res = response.json()

                # Проверяем ответ Baidu API
                if res.get("status") != 0:
                    message = (
                        f"API error: {res.get('message', 'Unknown error')}"
                    )
                    raise ValueError(message)

                results = res.get("results", [])

                if not results:
                    with log_path.open("a", encoding="utf-8") as logfile:
                        logfile.write(
                            f"{datetime.now():%Y-%m-%d %H:%M:%S} "
                            f"City={city_str}, page={page_num}, "
                            "No more results\n"
                        )
                    break

                with txt_path.open(
                    "a", encoding="utf-8", newline=""
                ) as file:
                    for item in results:
                        location = item.get("location") or {}

                        row = [
                            item.get("name", ""),
                            location.get("lng", ""),
                            location.get("lat", ""),
                            item.get("area", ""),
                            item.get("address", ""),
                        ]

                        # JSON корректно обрабатывает запятые
                        # и кавычки внутри текстовых полей
                        file.write(
                            json.dumps(row, ensure_ascii=False) + "\n"
                        )

                print(
                    f"Город: {city_str}, страница: {page_num}, "
                    f"найдено: {len(results)}"
                )

                page_num += 1
                time.sleep(1)

            except (requests.RequestException, ValueError) as exc:
                with log_path.open("a", encoding="utf-8") as logfile:
                    logfile.write(
                        f"{datetime.now():%Y-%m-%d %H:%M:%S} "
                        f"City={city_str}, page={page_num}, "
                        f"Error={exc}\n"
                    )

                print(f"Ошибка на странице {page_num}: {exc}")
                break

            except (KeyError, TypeError) as exc:
                with log_path.open("a", encoding="utf-8") as logfile:
                    logfile.write(
                        f"{datetime.now():%Y-%m-%d %H:%M:%S} "
                        f"City={city_str}, page={page_num}, "
                        f"Data error={exc}\n"
                    )

                print(f"Ошибка в данных API: {exc}")
                break
