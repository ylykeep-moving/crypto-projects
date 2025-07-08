import cv2
import numpy as np
import os


def embed_watermark(image, watermark_text):
    """嵌入文字水印到图像中"""
    watermark = np.zeros_like(image)
    font = cv2.FONT_HERSHEY_SIMPLEX
    position = (30, 60)
    font_scale = 1.5
    thickness = 2
    cv2.putText(watermark, watermark_text, position, font, font_scale, (255, 255, 255), thickness)

    # 图像融合：原图 + 水印（半透明）
    watermarked = cv2.addWeighted(image, 1.0, watermark, 0.4, 0)
    return watermarked, watermark


def extract_watermark(watermarked, original):
    """提取水印：对比差异"""
    diff = cv2.absdiff(watermarked, original)
    return diff


def apply_robustness_tests(image):
    """对图像执行各种扰动操作"""
    results = {}

    # 翻转
    results["flipped_horizontal"] = cv2.flip(image, 1)

    # 平移
    rows, cols = image.shape[:2]
    M = np.float32([[1, 0, 30], [0, 1, 30]])
    results["translated"] = cv2.warpAffine(image, M, (cols, rows))

    # 截取（裁剪中心区域）
    h, w = image.shape[:2]
    results["cropped"] = image[h // 4:3 * h // 4, w // 4:3 * w // 4]

    # 调整对比度
    results["contrast_adjusted"] = cv2.convertScaleAbs(image, alpha=1.8, beta=20)

    return results


def save_images(images_dict, prefix):
    os.makedirs(prefix, exist_ok=True)
    for name, img in images_dict.items():
        cv2.imwrite(f"{prefix}/{name}.png", img)


def main():
    # === 加载图像 ===
    original = cv2.imread('input.jpg')
    if original is None:
        print("无法读取 input.jpg，请放一张图片在程序目录下并重命名为 input.jpg")
        return

    # === 嵌入水印 ===
    watermarked, watermark = embed_watermark(original.copy(), "WATERMARK")
    cv2.imwrite("watermarked.png", watermarked)

    # === 提取水印 ===
    extracted = extract_watermark(watermarked, original)
    cv2.imwrite("extracted_watermark.png", extracted)

    # === 执行鲁棒性变换 ===
    transformed_images = apply_robustness_tests(watermarked)
    save_images(transformed_images, "robustness_outputs")

    # === 对鲁棒性图像尝试水印提取 ===
    for name, img in transformed_images.items():
        # 尺寸不一致时，调整为原图尺寸再提取
        if img.shape != original.shape:
            print(f"[警告] {name} 尺寸不同，已 resize 后再提取水印。")
            resized = cv2.resize(img, (original.shape[1], original.shape[0]))
            recovered = extract_watermark(resized, original)
        else:
            recovered = extract_watermark(img, original)

        cv2.imwrite(f"robustness_outputs/extracted_{name}.png", recovered)

    print("所有处理完成，结果已保存。")


if __name__ == "__main__":
    main()
