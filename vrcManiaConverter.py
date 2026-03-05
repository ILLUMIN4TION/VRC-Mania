import os
import urllib.parse # URL 특수문자(띄어쓰기 등) 완벽 변환용

# 📁 1. 최상위 곡 폴더 이름 (이 폴더 안에 4KEY, 7KEY 폴더가 있다고 가정)
root_folder = "Songs" 

# 🌐 2. 깃허브 RAW 최상위 주소 (Songs 폴더 직전까지만 적습니다!)
github_base_url = "https://raw.githubusercontent.com/ILLUMIN4TION/VRC-Mania/main/"

output_filename = "Playlist_VRCMania.txt"
song_count = 0

print("🔍 VRC-Mania .osu 파일 완전 자동 파싱을 시작합니다...\n")

with open(output_filename, "w", encoding="utf-8") as outfile:
    # 🌟 핵심: os.walk를 쓰면 폴더 안의 폴더까지 싹 다 뒤져서 찾아냅니다!
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith(".osu"):
                filepath = os.path.join(dirpath, filename)
                
                # 기본값 세팅
                title = "Unknown"
                artist = "Unknown"
                creator = "Unknown"
                version = "Normal"
                od = "5"
                hp = "5"
                
                # .osu 파일 읽기
                with open(filepath, "r", encoding="utf-8") as file:
                    for line in file:
                        line = line.strip()
                        if line.startswith("Title:"): title = line.split(":", 1)[1].strip()
                        elif line.startswith("Artist:"): artist = line.split(":", 1)[1].strip()
                        elif line.startswith("Creator:"): creator = line.split(":", 1)[1].strip()
                        elif line.startswith("Version:"): version = line.split(":", 1)[1].strip()
                        elif line.startswith("OverallDifficulty:"): od = line.split(":", 1)[1].strip()
                        elif line.startswith("HPDrainRate:"): hp = line.split(":", 1)[1].strip()
                        
                # 🌟 URL 자동 조립의 마술! 
                # 역슬래시(\)를 슬래시(/)로 바꿔서 완벽한 웹 경로를 만듭니다.
                # 예: Songs\4KEY\FAMoss\song.osu -> Songs/4KEY/FAMoss/song.osu
                relative_path = filepath.replace("\\", "/")
                
                # 띄어쓰기나 한글 등을 웹 표준(%20 등)으로 완벽하게 변환
                safe_path = urllib.parse.quote(relative_path)
                github_url = f"{github_base_url}{safe_path}"
                
                # 📝 데이터 합치기 (구분자 '|' 사용)
                # 순서: 제목 | 작곡가 | 맵퍼 | 난이도명 | OD | HP | 오디오URL | 깃허브URL
                line_to_write = f"{title}|{artist}|{creator}|{version}|{od}|{hp}|DROPBOX_AUDIO_HERE|{github_url}\n"
                outfile.write(line_to_write)
                
                print(f"✅ 완료: [{version}] {title} (OD:{od}, HP:{hp})")
                song_count += 1

print(f"\n🎉 대성공! 총 {song_count}개의 곡 데이터가 '{output_filename}'에 저장되었습니다!")