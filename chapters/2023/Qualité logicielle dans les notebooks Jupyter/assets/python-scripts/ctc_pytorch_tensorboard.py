#!/usr/bin/env python
# coding: utf-8

# # 导入必要的库

# In[1]:


import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision.transforms.functional import to_tensor, to_pil_image

from tensorboardX import SummaryWriter
import time
import matplotlib.pyplot as plt

from captcha.image import ImageCaptcha
from tqdm import tqdm
import random
import numpy as np
from collections import OrderedDict

import string
characters = '-' + string.digits + string.ascii_uppercase
width, height, n_len, n_classes = 192, 64, 4, len(characters)
n_input_length = 12
print(characters, width, height, n_len, n_classes)

%matplotlib auto

# # 搭建数据集

# In[2]:


class CaptchaDataset(Dataset):
    def __init__(self, characters, length, width, height, input_length, label_length):
        super(CaptchaDataset, self).__init__()
        self.characters = characters
        self.length = length
        self.width = width
        self.height = height
        self.input_length = input_length
        self.label_length = label_length
        self.n_class = len(characters)
        self.generator = ImageCaptcha(width=width, height=height)

    def __len__(self):
        return self.length
    
    def __getitem__(self, index):
        random_str = ''.join([random.choice(self.characters[1:]) for j in range(self.label_length)])
        image = to_tensor(self.generator.generate_image(random_str))
        target = torch.tensor([self.characters.find(x) for x in random_str], dtype=torch.long)
        input_length = torch.full(size=(1, ), fill_value=self.input_length, dtype=torch.long)
        target_length = torch.full(size=(1, ), fill_value=self.label_length, dtype=torch.long)
        return image, target, input_length, target_length

# # 测试数据集

# In[3]:


dataset = CaptchaDataset(characters, 1, width, height, n_input_length, n_len)
image, target, input_length, label_length = dataset[0]
print(''.join([characters[x] for x in target]), input_length, label_length)
to_pil_image(image)

# # 初始化数据集生成器

# In[4]:


batch_size = 128
train_set = CaptchaDataset(characters, 1000 * batch_size, width, height, n_input_length, n_len)
valid_set = CaptchaDataset(characters, 100 * batch_size, width, height, n_input_length, n_len)
train_loader = DataLoader(train_set, batch_size=batch_size, num_workers=12)
valid_loader = DataLoader(valid_set, batch_size=batch_size, num_workers=12)

# # 搭建模型

# In[5]:


class Model(nn.Module):
    def __init__(self, n_classes, input_shape=(3, 64, 128)):
        super(Model, self).__init__()
        self.input_shape = input_shape
        channels = [32, 64, 128, 256, 256]
        layers = [2, 2, 2, 2, 2]
        kernels = [3, 3, 3, 3, 3]
        pools = [2, 2, 2, 2, (2, 1)]
        modules = OrderedDict()
        
        def cba(name, in_channels, out_channels, kernel_size):
            modules[f'conv{name}'] = nn.Conv2d(in_channels, out_channels, kernel_size,
                                               padding=(1, 1) if kernel_size == 3 else 0)
            modules[f'bn{name}'] = nn.BatchNorm2d(out_channels)
            modules[f'relu{name}'] = nn.ReLU(inplace=True)
        
        last_channel = 3
        for block, (n_channel, n_layer, n_kernel, k_pool) in enumerate(zip(channels, layers, kernels, pools)):
            for layer in range(1, n_layer + 1):
                cba(f'{block+1}{layer}', last_channel, n_channel, n_kernel)
                last_channel = n_channel
            modules[f'pool{block + 1}'] = nn.MaxPool2d(k_pool)
        modules[f'dropout'] = nn.Dropout(0.25, inplace=True)
        
        self.cnn = nn.Sequential(modules)
        self.lstm = nn.LSTM(input_size=self.infer_features(), hidden_size=128, num_layers=2, bidirectional=True)
        self.fc = nn.Linear(in_features=256, out_features=n_classes)
    
    def infer_features(self):
        x = torch.zeros((1,)+self.input_shape)
        x = self.cnn(x)
        x = x.reshape(x.shape[0], -1, x.shape[-1])
        return x.shape[1]

    def forward(self, x):
        x = self.cnn(x)
        x = x.reshape(x.shape[0], -1, x.shape[-1])
        x = x.permute(2, 0, 1)
        x, _ = self.lstm(x)
        x = self.fc(x)
        return x

# ## 测试模型输出尺寸

# In[6]:


model = Model(n_classes, input_shape=(3, height, width))
inputs = torch.zeros((32, 3, height, width))
outputs = model(inputs)
outputs.shape

# ## 初始化模型

# In[7]:


now = time.strftime("%Y%m%d_%H%M%S", time.localtime())
model_name = f'crnn_{now}'
print(model_name)
writer = SummaryWriter(f'logs/{model_name}')

# In[8]:


model = Model(n_classes, input_shape=(3, height, width))
inputs = torch.zeros((1, 3, height, width))
writer.add_graph(model, inputs)

model = model.cuda()
model

# # 解码函数和准确率计算函数

# In[9]:


def decode(sequence):
    a = ''.join([characters[x] for x in sequence])
    s = ''.join([x for j, x in enumerate(a[:-1]) if x != characters[0] and x != a[j+1]])
    if len(s) == 0:
        return ''
    if a[-1] != characters[0] and s[-1] != a[-1]:
        s += a[-1]
    return s

def decode_target(sequence):
    return ''.join([characters[x] for x in sequence]).replace(' ', '')

def calc_acc(target, output):
    output_argmax = output.detach().permute(1, 0, 2).argmax(dim=-1)
    target = target.cpu().numpy()
    output_argmax = output_argmax.cpu().numpy()
    a = np.array([decode_target(true) == decode(pred) for true, pred in zip(target, output_argmax)])
    return a.mean()

# # 训练模型

# In[10]:


def train(model, optimizer, epoch, dataloader, writer):
    model.train()
    loss_mean = 0
    acc_mean = 0
    with tqdm(dataloader) as pbar:
        for batch_index, (data, target, input_lengths, target_lengths) in enumerate(pbar):
            data, target = data.cuda(), target.cuda()
            
            optimizer.zero_grad()
            output = model(data)
            
            output_log_softmax = F.log_softmax(output, dim=-1)
            loss = F.ctc_loss(output_log_softmax, target, input_lengths, target_lengths)
            
            loss.backward()
            optimizer.step()

            loss = loss.item()
            acc = calc_acc(target, output)
            
            iteration = (epoch - 1) * len(dataloader) + batch_index
            writer.add_scalar('train/loss', loss, iteration)
            writer.add_scalar('train/acc', acc, iteration)
            writer.add_scalar('train/error_rate', 1 - acc, iteration)
            
            if batch_index == 0:
                loss_mean = loss
                acc_mean = acc
            
            loss_mean = 0.1 * loss + 0.9 * loss_mean
            acc_mean = 0.1 * acc + 0.9 * acc_mean
            
            pbar.set_description(f'Epoch: {epoch} Loss: {loss_mean:.4f} Acc: {acc_mean:.4f} ')
    
    # draw badcase
    with torch.no_grad():
        output_argmax = output.detach().permute(1, 0, 2).argmax(dim=-1)
        loss = F.ctc_loss(output_log_softmax, target, input_lengths, target_lengths, reduction='none')
        hard_sample = np.argsort(loss.detach().cpu().numpy())[::-1]
        data = data.cpu()
        target = target.cpu()

        nrow = 4
        ncol = 4
        fig = plt.figure(figsize=(12, 6))
        for i, index in enumerate(hard_sample[:nrow*ncol]):
            plt.subplot(ncol, nrow, i+1)
            plt.axis('off')
            plt.imshow(data[index].numpy().transpose(1, 2, 0))
            s = f'true: {decode_target(target[index])}\npred: {decode(output_argmax[index])}'
            plt.title(s)

        fig.canvas.draw()
        image = np.array(fig.canvas.renderer.buffer_rgba())
        plt.close()
        writer.add_image('train/badcase', to_tensor(image), epoch)
    
    return loss_mean, acc_mean

def valid(model, epoch, dataloader, writer):
    model.eval()
    with tqdm(dataloader) as pbar, torch.no_grad():
        loss_sum = 0
        acc_sum = 0
        for batch_index, (data, target, input_lengths, target_lengths) in enumerate(pbar):
            data, target = data.cuda(), target.cuda()
            
            output = model(data)
            output_log_softmax = F.log_softmax(output, dim=-1)
            loss = F.ctc_loss(output_log_softmax, target, input_lengths, target_lengths)
            
            loss = loss.item()
            acc = calc_acc(target, output)
            
            loss_sum += loss
            acc_sum += acc
            
            loss_mean = loss_sum / (batch_index + 1)
            acc_mean = acc_sum / (batch_index + 1)
            
            pbar.set_description(f'Test : {epoch} Loss: {loss_mean:.4f} Acc: {acc_mean:.4f} ')
    return loss_mean, acc_mean

# In[11]:


optimizer = torch.optim.Adam(model.parameters(), 1e-4)
epochs = 30
for epoch in range(1, epochs + 1):
    train_loss, train_acc = train(model, optimizer, epoch, train_loader, writer)
    valid_loss, valid_acc = valid(model, epoch, valid_loader, writer)
    
    writer.add_scalars('epoch/loss', {'train': train_loss, 'valid': valid_loss}, epoch)
    writer.add_scalars('epoch/acc', {'train': train_acc, 'valid': valid_acc}, epoch)
    writer.add_scalars('epoch/error_rate', {'train': 1 - train_acc, 'valid': 1 - valid_acc}, epoch)

# In[12]:


optimizer = torch.optim.Adam(model.parameters(), 1e-5)
epochs2 = 10
for epoch in range(epochs, epochs + epochs2):
    train_loss, train_acc = train(model, optimizer, epoch, train_loader, writer)
    valid_loss, valid_acc = valid(model, epoch, valid_loader, writer)
    
    writer.add_scalars('epoch/loss', {'train': train_loss, 'valid': valid_loss}, epoch)
    writer.add_scalars('epoch/acc', {'train': train_acc, 'valid': valid_acc}, epoch)
    writer.add_scalars('epoch/error_rate', {'train': 1 - train_acc, 'valid': 1 - valid_acc}, epoch)

# # 测试模型输出

# In[18]:


model.eval()
do = True
while do or decode_target(target) == decode(output_argmax[0]):
    do = False
    image, target, input_length, label_length = dataset[0]

    output = model(image.unsqueeze(0).cuda())
    output_argmax = output.detach().permute(1, 0, 2).argmax(dim=-1)
#     print(f'true: {decode_target(target)} pred: {decode(output_argmax[0])}')

print(f'true: {decode_target(target)} pred: {decode(output_argmax[0])}')
print(''.join([characters[x] for x in output_argmax[0]]))
to_pil_image(image)

# In[19]:


torch.save(model, 'ctc.pth')

# In[ ]:



