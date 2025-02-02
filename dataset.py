import numpy as np
import json
from utils import token2vocab # utils 也是一个自己写的工具

# vocab - 必应词典
# 网络单词；词汇；生字

from miditok import CPWordEncoding

# [[MidiTok]]将MIDI音乐文件转换为令牌序列，即整数，准备好被馈送到序列神经网络，如[[transformer]]或[[rnn]]。
# [[miditok]]具有大多数已知的MIDI令牌化策略，并且围绕着它们都共享公共参数和方法的思想构建。
# 它包含允许正确预处理任何MIDI文件的方法，并且还支持字节对编码(BPE)。

# MidiTok使用MIDIToolkit，它本身使用Mido来读写MIDI文件。

# 也都是一些函数啊 



class CP_Word_Dataset(): 
    # cp是怎样的意思？CPWordEncoding
    # 这里是怎样一个处理方式？
    
    #     由复合词转换器引入的这种表示类似于REMI编码。
    # 关键的区别在于，同一“事件”的不同类型的标记由模型同时组合和处理。
    # 例如，同一音符的Pitch、Velocity和duration标记将被组合。
    # 这种编码策略的最大好处是减少了它创建的序列长度，这意味着更少的时间和内存消耗，因为变压器(具有softmax注意)具有二次复杂度。
    
    
    def __init__(self, dir, length, eos_tokens = None):
        self.dir = dir
        self.data = json.loads(open(self.dir, 'r').read())['data']
        self.length = length

        dataset_idx = [0]  # records the seq start index

        idx = 0
        bar_idx_final ={}
        for seq in self.data:
            seq = np.array(seq)
            seq_len = len(seq)
            bar_idx = np.where(seq[...,1] == 1)[0] # bar token
            
            bar_seq_len_final = len(np.where(bar_idx + length < seq_len)[0]) + 1
            bar_idx_final[idx] = bar_idx[:bar_seq_len_final]

            dataset_idx = np.append(
                dataset_idx, dataset_idx[-1] + bar_seq_len_final)
            idx+=1

        self.bar_idx_final = bar_idx_final
        self.dataset_idx = dataset_idx
        self.total_seq = dataset_idx[-1]
        self.eos_tokens = eos_tokens

    def get_seqs(self, idxs):

        return [token2vocab(self._getSeq(idx)) for idx in idxs]

    def _getSeq(self, idx):
        
        seq_n = np.where(self.dataset_idx > idx)[0][0] - 1

        bar_idx_n = self.bar_idx_final[seq_n]

        comsum_seq_count = self.dataset_idx[seq_n]

        start_idx = idx - comsum_seq_count

        final_start_idx = bar_idx_n[start_idx]

        r = self.data[seq_n][final_start_idx: final_start_idx + self.length] # (seq, last_dim)
        
        r = np.array(r)

        if r.shape[0] < self.length: # 

            r = np.concatenate([r, np.expand_dims(self.eos_tokens, 0)], 0)

            while r.shape[0] < self.length:
                pad_tokens = np.zeros((1, r.shape[-1]), dtype=np.int64)
                r = np.concatenate([r, pad_tokens], 0)

        return r
    
def get_tokenizer(): # 原来这个函数是自己定义的 
    pitch_range = range(21, 109)
    beat_res = {(0, 4): 8, (4, 12): 4}
    nb_velocities = 32

    additional_tokens = {
                    'Chord': True,
                    'Rest': True,
                    'Tempo': True,
                    'rest_range': (2, 8),  # (half, 8 beats)
                    'nb_tempos': 32,  # nb of tempo bins
                    'tempo_range': (40, 250),  # (min, max)
                    'Program':False,
                    }

    return CPWordEncoding(pitch_range, beat_res, nb_velocities, additional_tokens)