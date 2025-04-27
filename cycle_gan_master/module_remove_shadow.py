import torch 
import torch.nn as nn 
import torch.nn.functional as F
from torch.optim.lr_scheduler import LambdaLR
from torchvision.utils import save_image, make_grid
from torch.utils.tensorboard import SummaryWriter
import torchvision.transforms as transforms
from torch.utils.data import DataLoader

from cycle_gan_master.model import Generator, Discriminator, init_weights
from cycle_gan_master.utils import ImagePool,BasicDataset

from PIL import Image
from memory_profiler import profile

def remove_shadow_single_image(input_path, output_path):
    model = 'model_shadow_t'
    epoch = 200
    image_size = 256

    # set GPU or CPU
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # set depth of resnet
    res_block = 6 if image_size == 128 else 9

    # set models
    G_A2B = Generator(3, res_block).to(device)
    G_B2A = Generator(3, res_block).to(device)
    G_A2B.load_state_dict(torch.load(f"models/{model}/G_A2B/{epoch-1}.pth", map_location=device))
    G_B2A.load_state_dict(torch.load(f"models/{model}/G_B2A/{epoch-1}.pth", map_location=device))

    # Load and preprocess the input image
    input_image = Image.open(input_path).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize(int(image_size * 1.12), Image.BICUBIC),  # リサイズ
        transforms.CenterCrop(image_size),  # 中心クロップ
        transforms.ToTensor(),  # テンソル化
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])  # 正規化 [-1, 1]
    ])
    input_tensor = transform(input_image).unsqueeze(0).to(device)  # Add batch dimension

    # Perform inference
    with torch.no_grad():
        trans_B = G_B2A(input_tensor)  # Translated image
        input_tensor = (input_tensor * 0.5 + 0.5).clamp(0, 1)
        trans_B = (trans_B * 0.5 + 0.5).clamp(0, 1)
        save_image(trans_B, output_path, normalize=True)
        print(f"Translated image saved to {output_path}")


if __name__ == "__main__":
    # remove_shadow()

    input_image_path = "data/friend/testB/img_husuband_0494.jpg"  # 入力画像のパス
    output_image_path = "result/app/output_husuband_0494.jpg"  # 出力画像の保存先
    remove_shadow_single_image(input_image_path, output_image_path)