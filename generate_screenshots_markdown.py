import os

assets_dir = "docs/assets"
supported_exts = (".jpg", ".jpeg", ".JPG", ".JPEG")
for fname in sorted(os.listdir(assets_dir)):
    if fname.endswith(supported_exts):
        alt = os.path.splitext(fname)[0].replace("_", " ")
        print(f"![{alt}]({assets_dir}/{fname})")