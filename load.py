import torch
import torch.nn as nn
from torch.nn import functional as F
from bicl import *

device = 'cuda' if torch.cuda.is_available() else 'cpu'

torch.manual_seed(1337)

# wget https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt
with open('input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# here are all the unique characters that occur in this text
chars = sorted(list(set(text)))
vocab_size = len(chars)
# create a mapping from characters to integers
stoi = { ch:i for i,ch in enumerate(chars) }
itos = { i:ch for i,ch in enumerate(chars) }
encode = lambda s: [stoi[c] for c in s] # encoder: take a string, output a list of integers
decode = lambda l: ''.join([itos[i] for i in l]) # decoder: take a list of integers, output a string

m50K = torch.load('m50K.pt')

# generate from the model
context = torch.zeros((1, 1), dtype=torch.long, device=device)
print(decode(m50K.generate(context, max_new_tokens=500)[0].tolist()))
