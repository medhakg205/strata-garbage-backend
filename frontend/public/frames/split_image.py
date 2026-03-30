from PIL import Image
import os

def split_and_save():
    base_dir = r"C:\Users\mahak\OneDrive\strata-garbage-backend-main\frontend\public\frames"
    img_path = os.path.join(base_dir, "new_img1.jpg")
    
    # Open the 2x2 grid image
    img = Image.open(img_path)
    w, h = img.size
    
    # Calculate midpoints
    mid_w = w // 2
    mid_h = h // 2
    
    # Crop the 4 panels
    # define boxes: (left, upper, right, lower)
    top_left = img.crop((0, 0, mid_w, mid_h))
    top_right = img.crop((mid_w, 0, w, mid_h))
    bottom_left = img.crop((0, mid_h, mid_w, h))
    bottom_right = img.crop((mid_w, mid_h, w, h))
    
    # Save the individual frames
    top_left.save(os.path.join(base_dir, "anim_1.jpg"))
    top_right.save(os.path.join(base_dir, "anim_2.jpg"))
    bottom_left.save(os.path.join(base_dir, "anim_3.jpg"))
    bottom_right.save(os.path.join(base_dir, "anim_4.jpg"))
    
    print(f"Successfully split {w}x{h} image into 4 frames of {mid_w}x{mid_h}!")

if __name__ == "__main__":
    split_and_save()
