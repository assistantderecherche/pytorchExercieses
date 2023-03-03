Learning PyTorch along with Andrej Karpathy lecture:

"Let's build GPT: from scratch, in code, spelled out." https://youtu.be/kCc8FmEb1nY
Reference repo by the lecturer: https://github.com/karpathy/nanoGPT

The code is re-worked, some comments and assorted Pytorch exercises are added along the way
This work is done for training only and the better source of the same thing is quoted above.

m50.pt model:
	Trained using the v3.py version of the code
	Ran for 50K steps
	To run the m50.pt model:
		python load.py

	To re-train m50.pt model:
		python v3.py
		training is deterministic (seeds are set so you'll get the same model every time)
