from prototree.prototree import ProtoTree
from util.data import get_dataloaders
from util.visualize_prediction import gen_pred_vis
import argparse
import torch
import torchvision.transforms as transforms
from PIL import Image
from shutil import copy
from copy import deepcopy
import os
import unicodedata
from util.data import tokenization

def get_local_expl_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser('Explain a prediction')
    parser.add_argument('--prototree',
                        type=str,
                        help='Directory to trained ProtoTree')
    parser.add_argument('--log_dir',
                        type=str,
                        default='./runs/run_prototree',
                        help='The directory in which results should be logged. Should be same log_dir as loaded ProtoTree')
    parser.add_argument('--dataset',
                        type=str,
                        default='CUB-200-2011',
                        help='Data set on which the ProtoTree was trained')
    parser.add_argument('--dataset_pth',
                        type=str,
                        default='./data/CUB_200_2011',
                        help='The directory of CUB image dataset.')
    parser.add_argument('--text_pth',
                        type=str,
                        default='./text',
                        help='The directory that stores the CUB text files.')
    parser.add_argument('--pretrain_model',
                        type=str,
                        default='bert-base-cased',
                        help='The pretrained BERT model for tokenization and embedding.')
    parser.add_argument('--max_length',
                        type=int,
                        default=24,
                        help='The maximum length kept for each input texts.')
    parser.add_argument('--sample_dir',
                        type=str,
                        help='Directory to image to be explained, or to a folder containing multiple test images')
    parser.add_argument('--results_dir',
                        type=str,
                        default='local_explanations',
                        help='Directory where local explanations will be saved')
    parser.add_argument('--disable_cuda',
                        action='store_true',
                        help='Flag that disables GPU usage if set')
    parser.add_argument('--image_size',
                        type=int,
                        default=224,
                        help='Resize images to this size')
    parser.add_argument('--dir_for_saving_images',
                        type=str,
                        default='upsampling_results',
                        help='Directoy for saving the prototypes, patches and heatmaps')
    parser.add_argument('--upsample_threshold',
                        type=float,
                        default=0.98,
                        help='Threshold (between 0 and 1) for visualizing the nearest patch of an image after upsampling. The higher this threshold, the larger the patches.')
    args = parser.parse_args()
    return args


def get_sample_data(sample_dir):
    sample_data = []
    text = open(sample_dir, 'r').read()
    content = max(text.split('\n'), key=len)
    decode_content = unicodedata.normalize('NFKD', content).encode('ascii', 'replace').decode('utf-8')
    new_content = ' '.join(decode_content.split('??'))
    sample_data.append(new_content)
    return sample_data 


def explain_local(args):
    if not args.disable_cuda and torch.cuda.is_available():
        device = torch.device('cuda:{}'.format(torch.cuda.current_device()))
    else:
        device = torch.device('cpu')
        
    # Log which device was actually used
    print('Device used: ',str(device))

    # Load trained ProtoTree
    tree = ProtoTree.load(args.prototree).to(device=device)
    # Obtain the dataset and dataloaders
    args.batch_size=64 #placeholder
    args.augment = True #placeholder
    _, _, classes = get_dataloaders(args)
#     mean = (0.485, 0.456, 0.406)
#     std = (0.229, 0.224, 0.225)
#     normalize = transforms.Normalize(mean=mean,std=std)
#     test_transform = transform_no_augment = transforms.Compose([
#                         transforms.Resize(size=(args.image_size, args.image_size)),
#                         transforms.ToTensor(),
#                         normalize
#                     ])
    
#     sample = test_transform(Image.open(args.sample_dir)).unsqueeze(0).to(device)
    sample_texts = get_sample_data(args.sample_dir)
    sample_input_ids, sample_attention_masks = tokenization(sample_texts, args.max_length, pretrain_model='bert-base-cased')
    sample_input_ids, sample_attention_masks = sample_input_ids.to(device), sample_attention_masks.to(device)

    gen_pred_vis(tree, sample_input_ids, sample_attention_masks, args.sample_dir, args.results_dir, args, classes)



if __name__ == '__main__':
    args = get_local_expl_args()
    print("Texts to explain: ", args.sample_dir)
    explain_local(args)
#     try:
#         Image.open(args.sample_dir)
#         print("Texts to explain: ", args.sample_dir)
#         explain_local(args)
#     except: #folder is not image
#         class_name = args.sample_dir.split('/')[-1]
#         if not os.path.exists(os.path.join(os.path.join(args.log_dir, args.results_dir),class_name)):
#             os.makedirs(os.path.join(os.path.join(args.log_dir, args.results_dir),class_name))
#         for filename in os.listdir(args.sample_dir):
#             print(filename)
#             if filename.endswith(".jpg") or filename.endswith(".png"): 
#                 args_1 = deepcopy(args)
#                 args_1.sample_dir = args.sample_dir+"/"+filename
#                 args_1.results_dir = os.path.join(args.results_dir, class_name)
#                 explain_local(args_1)
