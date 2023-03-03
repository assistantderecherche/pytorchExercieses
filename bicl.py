import torch
import torch.nn as nn
from torch.nn import functional as F

# 
# hyperparameters (copied from gpt.py
#
batch_size = 64 # how many independent sequences will we process in parallel?
#block_size = 256 # what is the maximum context length for predictions?
block_size = 64 # what is the maximum context length for predictions?
device = 'cuda' if torch.cuda.is_available() else 'cpu'
#
# out of GPU ram
#n_embd = 384
n_embd = 96
#
#n_head = 6
n_head = 4
n_layer = 4
#n_layer = 6
dropout = 0.2
# ------------


# class Head was just copied from gpt.py
class Head(nn.Module):
    """ one head of self-attention """

    def __init__(self, head_size):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.register_buffer('tril', torch.tril(torch.ones(block_size, block_size)))

        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # input of size (batch, time-step, channels)
        # output of size (batch, time-step, head size)
        B,T,C = x.shape
        k = self.key(x)   # (B,T,hs)
        q = self.query(x) # (B,T,hs)
        # compute attention scores ("affinities")
        wei = q @ k.transpose(-2,-1) * k.shape[-1]**-0.5 # (B, T, hs) @ (B, hs, T) -> (B, T, T)
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float('-inf')) # (B, T, T)
        wei = F.softmax(wei, dim=-1) # (B, T, T)
        wei = self.dropout(wei)
        # perform the weighted aggregation of the values
        v = self.value(x) # (B,T,hs)
        out = wei @ v # (B, T, T) @ (B, T, hs) -> (B, T, hs)
        return out

class FeedForward(nn.Module):
    
    def __init__(self, n_embed):
        super().__init__()
        self.net = nn.Sequential(
                nn.Linear(n_embed, 4*n_embed),
                nn.ReLU(),
                nn.Linear(4*n_embed, n_embed)
        )
    def forward(self, x):
        return self.net(x)


class MultiHeadedAttention(nn.Module):

    def __init__(self, num_heads, head_size):
        super().__init__()

        # https://pytorch.org/docs/stable/generated/torch.nn.ModuleList.html
        # ModuleList can be indexed like a regular Python list, but modules it contains are properly registered, and will be visible by all Module methods.
        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])

        # so far not clear what this does
        # supposed to be an optimization for speeding training (???)
        self.proj = nn.Linear(n_embd, n_embd)
        # also a bit annoying using globals here, but maybe it's pythonic ;)

    # x is input, of course ;)
    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        out = self.proj(out)
        return out


class Block(nn.Module):

    def __init__(self, n_embed, n_heads):
        # darnit, why self is not passed into super().__init__()?
        # not the right place to check :)
        super().__init__()
        head_size = n_embed//n_heads
        self.sa = MultiHeadedAttention(n_heads, head_size)
        self.ffwd = FeedForward(n_embed)

    def forward(self, x):
        #
        # interestingly, in the lecture the first step is called
        #
        # COMMUNICATION
        x = x+self.sa(x)
        #
        # while the second is called
        #
        # COMPUTATION
        x = x+self.ffwd(x)
        # not sure about the subtle difference between the two
        return x


# super simple bigram model
class BigramLanguageModel(nn.Module):

    def __init__(self):
        super().__init__()
        # each token directly reads off the logits for the next token from a lookup table
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size, n_embd)

        # here different heads look at different portions of the 
        # token embedding (only some of the features are important to a given head
        # for example 'red features' as in Graves lecture

        # This is now replaced with a bunch of
        # sequential blocks
        #self.sa_heads = MultiHeadedAttention(n_head, n_embd//n_head)
        #self.ffwd = FeedForward(n_embd)

        #self.blocks = nn.Sequential(
        #        Block(n_embd, n_head), 
        #        Block(n_embd, n_head), 
        #        Block(n_embd, n_head)
        #)

        self.blocks = nn.Sequential(*[Block(n_embd, n_head) for _ in range(n_layer)])

        #
        # here we decode as we go from 
        # the embedding size (384 in this case) to vocab_size (65 for Shakespeare)
        #
        self.lm_head = nn.Linear(n_embd, vocab_size)

    def forward(self, idx, targets=None):
        B,T = idx.shape # batch, time

        # idx and targets are both (B,T) tensor of integers
        tok_emb = self.token_embedding_table(idx) # (B,T,C == n_embd)

        pos_emb = self.position_embedding_table(torch.arange(T, device=device)) # (T, C) 

        # broadcasting: (makes sense as the offsets aren't different between batches
        x = tok_emb+pos_emb # (B,T,C)

        # here multiheaded self-attention comes in as an extra transformation:

        x = self.blocks(x)
        #x = self.sa_heads(x)
        #x = self.ffwd.net(x)

        logits = self.lm_head(x) # (B,T,C == vocab_size)

        if targets is None:
            loss = None
        else:
            B, T, C = logits.shape
            logits = logits.view(B*T, C)
            targets = targets.view(B*T)
            loss = F.cross_entropy(logits, targets)

        return logits, loss

    def generate(self, idx, max_new_tokens):
        # idx is (B, T) array of indices in the current context
        for _ in range(max_new_tokens):
            # crop idx to the last block_size tokens
            idx_cond = idx[:, -block_size:]
            # get the predictions
            logits, loss = self(idx_cond)
            # focus only on the last time step
            logits = logits[:, -1, :] # becomes (B, C)
            # apply softmax to get probabilities
            probs = F.softmax(logits, dim=-1) # (B, C)
            # sample from the distribution
            idx_next = torch.multinomial(probs, num_samples=1) # (B, 1)
            # append sampled index to the running sequence
            idx = torch.cat((idx, idx_next), dim=1) # (B, T+1)
        return idx
