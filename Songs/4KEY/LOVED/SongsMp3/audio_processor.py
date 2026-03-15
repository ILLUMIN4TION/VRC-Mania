import os
import re
import subprocess
import json

# ==========================================
# ⚙️ 설정 부분 (R2 최적화 및 강제 압축)
# ==========================================
MAPS_FOLDER = ".."                    
OUTPUT_FOLDER = "./Export_R2"         
CATEGORY_PREFIX = "L"                 
DEFAULT_RATES = [0.75, 1.5]           

# 🚨 본인의 R2 퍼블릭 주소
R2_BASE_URL = "https://pub-520fa580f2ea459b8a567fee74f1a236.r2.dev"

def clean_string_for_filename(s):
    s = re.sub(r'[\\/*?:"<>|]', "", s)
    return s.strip().replace(" ", "_")

def scan_and_process():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    print("🔍 맵 폴더들을 스캔하여 메타데이터와 오디오를 분석합니다...")
    folder_data = {}
    
    # 1. 맵 폴더 스캔 및 배속 감지
    for root, dirs, files in os.walk(MAPS_FOLDER):
        if "Export_" in root or "SongsMp3" in root:
            continue
            
        folder_name = os.path.basename(root)
        for file in files:
            if file.endswith(".osu"):
                osu_path = os.path.join(root, file)
                try:
                    with open(osu_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        title_match = re.search(r'^Title:(.+)$', content, re.MULTILINE)
                        audio_match = re.search(r'^AudioFilename:\s*(.+)$', content, re.MULTILINE)
                        version_match = re.search(r'^Version:(.+)$', content, re.MULTILINE)
                        
                        if not title_match or not audio_match: continue
                            
                        original_title = title_match.group(1).strip()
                        audio_filename = audio_match.group(1).strip()
                        version_str = version_match.group(1).strip() if version_match else ""
                        audio_path = os.path.join(root, audio_filename)
                        if not os.path.exists(audio_path): continue 
                            
                        rate_val = 1.0
                        search_target = f"{version_str} {file}"
                        rate_match = re.search(r'(?i)(?:x\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*x)', search_target)
                        
                        if rate_match:
                            val_str = rate_match.group(1) or rate_match.group(2)
                            try: rate_val = float(val_str)
                            except ValueError: pass
                        else:
                            audio_float_match = re.search(r'(?i)[_ \-](\d+\.\d+)', audio_filename)
                            if audio_float_match:
                                try: rate_val = float(audio_float_match.group(1))
                                except ValueError: pass
                            else:
                                audio_int_match = re.search(r'(?i)audio(\d{3})\.mp3', audio_filename)
                                if audio_int_match:
                                    try: rate_val = float(audio_int_match.group(1)) / 100.0
                                    except ValueError: pass

                        if folder_name not in folder_data:
                            folder_data[folder_name] = {"title": original_title, "audios": {}}
                        if audio_filename not in folder_data[folder_name]["audios"]:
                            folder_data[folder_name]["audios"][audio_filename] = {"audio_path": audio_path, "rates_found": set()}
                        folder_data[folder_name]["audios"][audio_filename]["rates_found"].add(rate_val)

                except Exception as e: print(f"⚠️ {file} 읽기 오류: {e}")

    # 2. 모든 파일 128kbps 강제 압축 및 배속 생성
    json_output = {}
    index = 1
    
    for folder_name, data in sorted(folder_data.items()):
        new_id = f"{CATEGORY_PREFIX}{index:03d}"
        safe_title = clean_string_for_filename(data["title"])
        json_output[folder_name] = {}
        
        print(f"\n📁 [{new_id}] '{folder_name}' 처리 중...")
        total_audios = len(data["audios"])
        
        for audio_filename, audio_info in data["audios"].items():
            audio_path = audio_info["audio_path"]
            rates_found = audio_info["rates_found"]
            is_base = (1.0 in rates_found) or (total_audios == 1)
            
            safe_audio = clean_string_for_filename(os.path.splitext(audio_filename)[0])
            final_base_name = f"{new_id}_{safe_title}_{safe_audio}"
            _, ext = os.path.splitext(audio_path)
            urls = {}
            
            # 🎵 [핵심 변경점] 원본이나 매퍼 배속 파일도 단순 복사가 아닌 128k 압축 진행!
            original_output = f"{final_base_name}{ext}"
            original_output_path = os.path.join(OUTPUT_FOLDER, original_output)
            
            print(f"  🎵 [압축 중] {audio_filename} -> 128kbps 변환 중...")
            command_base = [
                "ffmpeg", "-y", "-i", audio_path, 
                "-b:a", "128k",  # 128kbps 비트레이트 제한
                original_output_path
            ]
            try:
                subprocess.run(command_base, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                urls["1.0"] = f"{R2_BASE_URL}/{original_output}"
            except subprocess.CalledProcessError as e:
                print(f"  ❌ 압축 실패: {e}")
            
            # [HT/DT 생성] 정배속 파일일 경우 추가 생성
            if is_base:
                print(f"  🎵 [HT/DT 생성] {audio_filename} -> 0.75x, 1.5x (128kbps) 생성 중...")
                for rate in DEFAULT_RATES:
                    output_filename = f"{final_base_name}_{rate}x{ext}"
                    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                    
                    audio_filter = f"atempo={rate}" if rate < 1.0 else f"asetrate=44100*{rate},aresample=44100"
                    
                    command_rate = [
                        "ffmpeg", "-y", "-i", audio_path, 
                        "-filter:a", audio_filter, 
                        "-b:a", "128k", # HT/DT 파일도 128kbps 비트레이트 제한
                        output_path
                    ]
                    try:
                        subprocess.run(command_rate, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        urls[str(rate)] = f"{R2_BASE_URL}/{output_filename}"
                    except subprocess.CalledProcessError as e:
                        print(f"  ❌ {rate}x 생성 실패: {e}")
            else:
                detected_rates = ", ".join([f"{r}x" for r in rates_found])
                print(f"  ⏩ [배속맵 감지: {detected_rates}] HT/DT 생성을 건너뜀.")
            
            json_output[folder_name][audio_filename] = {
                "title": data["title"],
                "id": new_id,
                "is_base": is_base,
                "urls": urls
            }
        index += 1

    with open(os.path.join(OUTPUT_FOLDER, "songs_map_data.json"), 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=4, ensure_ascii=False)
        
    print(f"\n🎉 [작업 완료] 모든 파일이 128kbps로 다이어트에 성공했습니다!")

if __name__ == "__main__":
    scan_and_process()