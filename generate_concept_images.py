#!/usr/bin/env python3
"""
TIBY 제품 컨셉사진 생성기
- Google Drive에서 제품 누끼사진을 다운로드
- Shopify CDN 누끼사진 fallback 지원
- OpenAI gpt-image-1 API로 컨셉 이미지 생성
"""

import os
import sys
import base64
import io
import time
from pathlib import Path

import gdown
import requests
from openai import OpenAI
from PIL import Image

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GDRIVE_FOLDER_ID = "137nSZPMToNsbX_CZrMRCkqbYt4Jr6LFs"

BASE_DIR = Path(__file__).parent
NUKKI_DIR = BASE_DIR / "nukki_images"
CONCEPT_DIR = BASE_DIR / "concept_images"

# Shopify CDN 누끼사진 URL (Google Drive 실패 시 fallback)
SHOPIFY_NUKKI = {
    "LOVE_ME_ME": [
        ("LOVE_ME_ME_pink_front.png", "https://cdn.shopify.com/s/files/1/0948/3173/9160/files/LOVE_ME_ME_pink_front1_1.png"),
        ("LOVE_ME_ME_pink_side.png", "https://cdn.shopify.com/s/files/1/0948/3173/9160/files/LOVE_ME_ME_pink_side_2.png"),
    ],
    "HUG_ME_ME": [
        ("HUG_ME_ME_green_front.png", "https://cdn.shopify.com/s/files/1/0948/3173/9160/files/LOVE_ME_ME_Green_front1_3.png"),
        ("HUG_ME_ME_green_side.png", "https://cdn.shopify.com/s/files/1/0948/3173/9160/files/LOVE_ME_ME_Green_side_1.png"),
    ],
    "KISS_ME_ME": [
        ("KISS_ME_ME_purple_front.png", "https://cdn.shopify.com/s/files/1/0948/3173/9160/files/LOVE_ME_ME_purple_front1_1.png"),
        ("KISS_ME_ME_purple_side.png", "https://cdn.shopify.com/s/files/1/0948/3173/9160/files/LOVE_ME_ME_purple_side_1.png"),
    ],
}

# 제품 정보 및 컨셉 프롬프트
PRODUCTS = {
    "LOVE_ME_ME": {
        "name": "LOVE ME ME (ラブ ミーミー)",
        "color": "pink / rose gold",
        "scent": "Bergamot, Orange, Peach top → Orchid, Rose, Jasmine mid → Musk, Amber base",
        "mood": "romantic, dreamy, feminine",
        "concepts": [
            {
                "name": "cherry_blossom_date",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'LOVE ME ME' pink hair perfume bottle elegantly on a marble surface "
                    "under cherry blossom trees in full bloom. "
                    "Soft pink petals are gently falling around the bottle. "
                    "Golden hour sunlight creates warm, romantic lighting. "
                    "Background shows a dreamy bokeh of cherry blossoms. "
                    "Style: high-end cosmetics advertisement photography, editorial beauty shot, "
                    "soft focus, pastel pink color palette, luxurious and romantic mood. "
                    "The bottle must match the reference exactly - same shape, color, label."
                ),
            },
            {
                "name": "romantic_vanity",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'LOVE ME ME' pink hair perfume bottle "
                    "on an elegant vintage vanity table with a rose gold mirror. "
                    "Surrounded by fresh pink roses, peach blossoms, and delicate orchids. "
                    "Soft morning light streaming through sheer curtains. "
                    "Pearl jewelry and silk ribbon scattered artfully nearby. "
                    "Style: high-end beauty editorial photography, soft dreamy lighting, "
                    "warm pink and gold tones, luxury cosmetics campaign. "
                    "The bottle must match the reference exactly."
                ),
            },
            {
                "name": "sunset_rooftop",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'LOVE ME ME' pink hair perfume bottle on a glass table "
                    "at a stylish rooftop bar during golden sunset. "
                    "City skyline silhouetted in the warm background. "
                    "Rose petals and a champagne glass beside the bottle. "
                    "Warm sunset light creates beautiful reflections on the glass bottle. "
                    "Style: lifestyle luxury brand photography, warm golden hour lighting, "
                    "sophisticated urban romance, editorial beauty campaign. "
                    "The bottle must match the reference exactly."
                ),
            },
        ],
    },
    "HUG_ME_ME": {
        "name": "HUG ME ME (ハグ ミーミー)",
        "color": "green / teal",
        "scent": "Fresh citrus top → Green tea, White flowers mid → Vanilla, Sandalwood base",
        "mood": "fresh, calming, natural, cozy",
        "concepts": [
            {
                "name": "botanical_garden",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'HUG ME ME' green/teal hair perfume bottle "
                    "on a mossy stone in a lush botanical garden setting. "
                    "Surrounded by fresh green ferns, eucalyptus leaves, and white wildflowers. "
                    "Soft dappled sunlight filtering through the canopy above. "
                    "Morning dew droplets visible on nearby leaves. "
                    "Style: high-end natural beauty photography, fresh green color palette, "
                    "organic luxury aesthetic, editorial beauty campaign. "
                    "The bottle must match the reference exactly."
                ),
            },
            {
                "name": "cozy_cafe",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'HUG ME ME' green hair perfume bottle "
                    "on a wooden cafe table next to a matcha latte and an open book. "
                    "A cozy cafe interior with green plants hanging from the ceiling. "
                    "Natural light from a large window illuminates the scene. "
                    "Warm, inviting atmosphere with earth tones and green accents. "
                    "Style: lifestyle brand photography, warm natural lighting, "
                    "Scandinavian minimalist aesthetic, cozy and sophisticated mood. "
                    "The bottle must match the reference exactly."
                ),
            },
            {
                "name": "zen_morning",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'HUG ME ME' green hair perfume bottle "
                    "on a smooth river stone beside a small zen garden arrangement. "
                    "Fresh green tea leaves and white jasmine flowers scattered around. "
                    "Soft morning mist in the background, creating a serene atmosphere. "
                    "Clean white linen fabric draped underneath. "
                    "Style: luxury zen beauty photography, calming green and white palette, "
                    "Japanese minimalist aesthetic, high-end skincare campaign. "
                    "The bottle must match the reference exactly."
                ),
            },
        ],
    },
    "KISS_ME_ME": {
        "name": "KISS ME ME (キス ミーミー)",
        "color": "purple / lavender",
        "scent": "Apple, Raspberry top → Violet, Iris, Peony mid → Woody, Musk base",
        "mood": "mysterious, elegant, sophisticated",
        "concepts": [
            {
                "name": "twilight_elegance",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'KISS ME ME' purple/lavender hair perfume bottle "
                    "on a dark marble surface with dramatic twilight lighting. "
                    "Purple velvet fabric draped elegantly in the background. "
                    "Fresh purple iris flowers and dark berries arranged artfully beside the bottle. "
                    "Moody, sophisticated lighting with purple and silver accents. "
                    "Style: high-end luxury perfume advertisement, dramatic studio lighting, "
                    "deep purple and silver color palette, mysterious and elegant mood. "
                    "The bottle must match the reference exactly."
                ),
            },
            {
                "name": "night_restaurant",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'KISS ME ME' purple hair perfume bottle "
                    "on an elegant restaurant table with candlelight. "
                    "Dark wood table with a glass of red wine nearby. "
                    "Soft purple ambient lighting, bokeh city lights visible through the window. "
                    "A single violet flower resting beside the bottle. "
                    "Style: luxury lifestyle photography, moody evening ambiance, "
                    "deep purple and warm gold tones, upscale dining aesthetic. "
                    "The bottle must match the reference exactly."
                ),
            },
            {
                "name": "moonlit_garden",
                "prompt": (
                    "Use the provided product photo as exact reference for the bottle design. "
                    "Place this exact TIBY 'KISS ME ME' purple hair perfume bottle "
                    "on an antique stone pedestal in a moonlit garden. "
                    "Lavender bushes and purple wisteria cascading in the background. "
                    "Soft moonlight creating an ethereal, magical atmosphere. "
                    "Fireflies or soft light particles floating in the air. "
                    "Style: fantasy beauty editorial photography, ethereal moonlight, "
                    "deep purple and silver palette, enchanting and luxurious mood. "
                    "The bottle must match the reference exactly."
                ),
            },
        ],
    },
}


def download_from_gdrive(folder_id: str, output_dir: Path) -> list[Path]:
    """Google Drive 공유 폴더에서 모든 이미지를 다운로드합니다."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'─' * 50}")
    print(f"📂 Google Drive에서 누끼사진 다운로드 중...")
    print(f"   폴더 ID: {folder_id}")
    print(f"   저장 경로: {output_dir}\n")

    url = f"https://drive.google.com/drive/folders/{folder_id}"
    try:
        downloaded = gdown.download_folder(
            url=url,
            output=str(output_dir),
            quiet=False,
            use_cookies=False,
        )
        if downloaded:
            files = [Path(f) for f in downloaded if Path(f).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
            print(f"\n✅ Google Drive: {len(files)}개 이미지 다운로드 완료")
            for f in files:
                print(f"   - {Path(f).name}")
            return files
        else:
            print("⚠️  Google Drive에서 다운로드된 파일이 없습니다.")
            return []
    except Exception as e:
        print(f"⚠️  Google Drive 다운로드 실패: {e}")
        return []


def download_from_shopify_cdn(output_dir: Path) -> list[Path]:
    """Shopify CDN에서 기존 누끼사진을 다운로드합니다 (fallback)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded_files = []

    print(f"\n{'─' * 50}")
    print(f"🔄 Shopify CDN에서 기존 누끼사진 다운로드 중 (fallback)...\n")

    for product_key, urls in SHOPIFY_NUKKI.items():
        for filename, url in urls:
            output_path = output_dir / filename
            if output_path.exists():
                print(f"   ✓ 이미 존재: {filename}")
                downloaded_files.append(output_path)
                continue
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                print(f"   ✅ 다운로드: {filename}")
                downloaded_files.append(output_path)
            except Exception as e:
                print(f"   ❌ 실패: {filename} - {e}")

    return downloaded_files


def match_nukki_to_products(nukki_files: list[Path]) -> dict[str, list[Path]]:
    """다운로드된 누끼사진을 제품별로 매칭합니다."""
    mapping = {key: [] for key in PRODUCTS}

    keywords = {
        "LOVE_ME_ME": ["love", "pink"],
        "HUG_ME_ME": ["hug", "green"],
        "KISS_ME_ME": ["kiss", "purple"],
    }

    for f in nukki_files:
        name_lower = f.name.lower()
        matched = False
        for product_key, kws in keywords.items():
            if any(kw in name_lower for kw in kws):
                mapping[product_key].append(f)
                matched = True
                break
        if not matched:
            for key in mapping:
                mapping[key].append(f)

    return mapping


def prepare_image_for_api(image_path: Path, max_size: int = 1024) -> bytes:
    """이미지를 API 전송에 적합한 형식으로 준비합니다."""
    img = Image.open(image_path)

    # RGBA → RGB 변환 (투명배경을 흰색으로)
    if img.mode == "RGBA":
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # 리사이즈
    w, h = img.size
    if max(w, h) > max_size:
        ratio = max_size / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_concept_image(
    client: OpenAI,
    prompt: str,
    nukki_path: Path | None = None,
    output_path: Path = Path("output.png"),
    size: str = "1024x1536",
) -> Path | None:
    """OpenAI gpt-image-1 API로 컨셉 이미지를 생성합니다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 누끼사진이 있으면 이미지 편집 모드 (참조 이미지 사용)
        if nukki_path and nukki_path.exists():
            image_bytes = prepare_image_for_api(nukki_path)

            result = client.images.edit(
                model="gpt-image-1",
                image=image_bytes,
                prompt=prompt,
                n=1,
                size=size,
            )
        else:
            # 누끼사진 없으면 텍스트만으로 생성
            result = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                n=1,
                size=size,
                quality="high",
            )

        # 결과 저장
        if result.data:
            img_data = result.data[0]

            if hasattr(img_data, "b64_json") and img_data.b64_json:
                img_bytes = base64.b64decode(img_data.b64_json)
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                return output_path

            if hasattr(img_data, "url") and img_data.url:
                resp = requests.get(img_data.url, timeout=120)
                resp.raise_for_status()
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return output_path

        print("⚠️  이미지 데이터가 비어있습니다.")
        return None

    except Exception as e:
        print(f"❌ 이미지 생성 실패: {e}")
        return None


def main():
    # ── API 키 확인 ──
    api_key = OPENAI_API_KEY
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        print()
        print("   실행 방법:")
        print("   OPENAI_API_KEY='sk-...' python3 generate_concept_images.py")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print("=" * 60)
    print("  🧴 TIBY 제품 컨셉사진 생성기")
    print("=" * 60)

    # ── 1. 누끼사진 다운로드 ──
    # 먼저 Google Drive 시도
    nukki_files = download_from_gdrive(GDRIVE_FOLDER_ID, NUKKI_DIR)

    # Google Drive 실패 시 Shopify CDN fallback
    if not nukki_files:
        print("\n   → Shopify CDN fallback으로 전환합니다.")
        nukki_files = download_from_shopify_cdn(NUKKI_DIR)

    if not nukki_files:
        print("\n❌ 누끼사진을 다운로드할 수 없습니다.")
        print("   nukki_images/ 폴더에 직접 누끼사진을 넣고 다시 실행해주세요.")
        sys.exit(1)

    # ── 2. 제품별 매칭 ──
    product_nukki_map = match_nukki_to_products(nukki_files)

    print(f"\n{'─' * 50}")
    print("📋 제품별 누끼사진 매칭 결과:")
    for product_key, files in product_nukki_map.items():
        product_name = PRODUCTS[product_key]["name"]
        print(f"   {product_name}: {len(files)}개")
        for f in files:
            print(f"     └ {f.name}")

    # ── 3. 컨셉 이미지 생성 ──
    CONCEPT_DIR.mkdir(parents=True, exist_ok=True)
    generated = []

    total_concepts = sum(len(p["concepts"]) for p in PRODUCTS.values())
    current = 0

    for product_key, product_info in PRODUCTS.items():
        nukki_list = product_nukki_map.get(product_key, [])
        nukki_path = nukki_list[0] if nukki_list else None

        product_dir = CONCEPT_DIR / product_key.lower()
        product_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'═' * 50}")
        print(f"🎨 {product_info['name']} 컨셉사진 생성 중...")
        if nukki_path:
            print(f"   참조 누끼사진: {nukki_path.name}")
        else:
            print(f"   ⚠️  누끼사진 없음 → 텍스트 프롬프트만으로 생성")

        for concept in product_info["concepts"]:
            current += 1
            concept_name = concept["name"]
            output_path = product_dir / f"{concept_name}.png"

            print(f"\n   [{current}/{total_concepts}] {concept_name}")
            print(f"   생성 중... ", end="", flush=True)

            result = generate_concept_image(
                client=client,
                prompt=concept["prompt"],
                nukki_path=nukki_path,
                output_path=output_path,
            )

            if result:
                print(f"✅ 저장됨")
                print(f"     └ {result.relative_to(BASE_DIR)}")
                generated.append(result)
            else:
                print("❌ 실패")

            # API rate limit 방지
            time.sleep(3)

    # ── 4. 결과 요약 ──
    print(f"\n{'═' * 60}")
    print(f"  🎉 컨셉사진 생성 완료!")
    print(f"  총 {len(generated)}/{total_concepts}개 생성됨")
    print(f"  저장 위치: {CONCEPT_DIR.relative_to(BASE_DIR)}/")
    print(f"{'═' * 60}\n")

    for product_key in PRODUCTS:
        product_dir = CONCEPT_DIR / product_key.lower()
        imgs = sorted(product_dir.glob("*.png"))
        if imgs:
            print(f"  📁 {product_key.lower()}/")
            for img in imgs:
                size_kb = img.stat().st_size / 1024
                print(f"     📸 {img.name} ({size_kb:.0f}KB)")

    return generated


if __name__ == "__main__":
    main()
