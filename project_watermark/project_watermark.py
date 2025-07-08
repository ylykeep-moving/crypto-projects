import cv2
import numpy as np
from scipy.fftpack import dct, idct
import os

# ========== watermark_embed.py ==========
def embed_watermark(host_img_path, watermark_img_path, alpha=10):
    host = cv2.imread(host_img_path, cv2.IMREAD_GRAYSCALE)
    watermark = cv2.imread(watermark_img_path, cv2.IMREAD_GRAYSCALE)
    watermark = cv2.resize(watermark, (32, 32))

    h_dct = dct(dct(host.astype(float), axis=0, norm='ortho'), axis=1, norm='ortho')
    wm_dct = watermark / 255.0

    h_dct[100:132, 100:132] += alpha * wm_dct
    watermarked = idct(idct(h_dct, axis=1, norm='ortho'), axis=0, norm='ortho')

    return np.clip(watermarked, 0, 255).astype(np.uint8)


# ========== watermark_extract.py ==========
def extract_watermark(watermarked_img_path, original_img_path, alpha=10):
    watermarked = cv2.imread(watermarked_img_path, cv2.IMREAD_GRAYSCALE)
    original = cv2.imread(original_img_path, cv2.IMREAD_GRAYSCALE)

    w_dct = dct(dct(watermarked.astype(float), axis=0, norm='ortho'), axis=1, norm='ortho')
    o_dct = dct(dct(original.astype(float), axis=0, norm='ortho'), axis=1, norm='ortho')

    wm_dct = (w_dct[100:132, 100:132] - o_dct[100:132, 100:132]) / alpha
    wm_img = np.clip(wm_dct * 255.0, 0, 255).astype(np.uint8)

    return wm_img


# ========== attacks.py ==========
def flip_attack(img):
    return cv2.flip(img, 1)

def shift_attack(img, dx=20, dy=10):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))

def crop_attack(img, crop_size=50):
    h, w = img.shape
    return img[crop_size:h-crop_size, crop_size:w-crop_size]

def contrast_attack(img, factor=1.5):
    return np.clip(img * factor, 0, 255).astype(np.uint8)

def gaussian_blur_attack(img, ksize=5):
    return cv2.GaussianBlur(img, (ksize, ksize), 0)


# ========== test_main.py ==========
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def main():
    host = "images/host.jpg"
    wm = "images/watermark.png"
    output_dir = "images/output"
    ensure_dir(output_dir)

    watermarked = embed_watermark(host, wm)
    cv2.imwrite(f"{output_dir}/watermarked.jpg", watermarked)

    # 攻击
    flipped = flip_attack(watermarked)
    shifted = shift_attack(watermarked)
    cropped = crop_attack(watermarked)
    contrast = contrast_attack(watermarked)
    blurred = gaussian_blur_attack(watermarked)

    # 保存攻击图像
    cv2.imwrite(f"{output_dir}/flipped.jpg", flipped)
    cv2.imwrite(f"{output_dir}/shifted.jpg", shifted)
    cv2.imwrite(f"{output_dir}/cropped.jpg", cropped)
    cv2.imwrite(f"{output_dir}/contrast.jpg", contrast)
    cv2.imwrite(f"{output_dir}/blurred.jpg", blurred)

    # 提取水印
    extracted = extract_watermark(f"{output_dir}/watermarked.jpg", host)
    cv2.imwrite(f"{output_dir}/extracted.jpg", extracted)

if __name__ == "__main__":
    main()
