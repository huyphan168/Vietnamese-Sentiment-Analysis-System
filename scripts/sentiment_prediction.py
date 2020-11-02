from pymongo import MongoClient
import torch
import torchtext
import torch.nn as nn
import numpy as np
import torch.nn.functional as F
import re
import string
import codecs
from pyvi import ViTokenizer
import pickle

class VSA_BiLSTM(nn.Module):
  def __init__(self, vocab_size, emb_size=300, hidden_size=512):
    super(VSA_BiLSTM, self).__init__()
    self.embedding = nn.Embedding(vocab_size, emb_size)
    self.hidden_size = hidden_size
    self.lstm = nn.LSTM(input_size=emb_size,
                        hidden_size=self.hidden_size,
                        num_layers=2,
                        batch_first=True,
                        bidirectional=True)
    self.dropout = nn.Dropout(p=0.5)

    self.fc = nn.Linear(2*self.hidden_size,3)
  def forward(self, text):
    #Text = [Batch_size, seq_len]
    text_emb = self.embedding(text)
    #Text_emb = [Batch_size, seq_len, emb_dim]
    output, (hidden, cell) = self.lstm(text_emb)
    #output = [Batch_Size, seq_len, hidden_size*directions]
    output_forward = torch.squeeze(output[:, -1, :self.hidden_size], 1)
    output_backward = torch.squeeze(output[:, -1, self.hidden_size:], 1)
    out_bidirectional = torch.cat((output_forward, output_backward), 1)
    out_dropped = self.dropout(out_bidirectional)
    return self.fc(out_dropped)

def read_vocab(path):
    vocab_file = open(path, "rb")
    vocab = pickle.load(vocab_file)
    return vocab

def get_input():
    client = MongoClient('mongodb://database:27017')
    db = client.database_devC
    unlabel_comments = db.find({"Label": ""})
    
      

class Estimator():
  def __init__(self, weight_path, vocab_path):
    self.vocab = read_vocab(vocab_path)
    self.size_vocab = len(self.vocab)
    self.model = VSA_BiLSTM(self.size_vocab)
    self.model.load_state_dict(
      torch.load(weight_path, map_location=torch.device('cpu')))
    self.model.to("cpu")

  def normalize_text(self,text):

    #Remove các ký tự kéo dài: vd: đẹppppppp
    text = re.sub(r'([A-Z])\1+', lambda m: m.group(1).upper(), text, flags=re.IGNORECASE)

    # Chuyển thành chữ thường
    text = text.lower()

    #Chuẩn hóa tiếng Việt, xử lý emoj, chuẩn hóa tiếng Anh, thuật ngữ
    replace_list = {
        'òa': 'oà', 'óa': 'oá', 'ỏa': 'oả', 'õa': 'oã', 'ọa': 'oạ', 'òe': 'oè', 'óe': 'oé','ỏe': 'oẻ',
        'õe': 'oẽ', 'ọe': 'oẹ', 'ùy': 'uỳ', 'úy': 'uý', 'ủy': 'uỷ', 'ũy': 'uỹ','ụy': 'uỵ', 'uả': 'ủa',
        'ả': 'ả', 'ố': 'ố', 'u´': 'ố','ỗ': 'ỗ', 'ồ': 'ồ', 'ổ': 'ổ', 'ấ': 'ấ', 'ẫ': 'ẫ', 'ẩ': 'ẩ',
        'ầ': 'ầ', 'ỏ': 'ỏ', 'ề': 'ề','ễ': 'ễ', 'ắ': 'ắ', 'ủ': 'ủ', 'ế': 'ế', 'ở': 'ở', 'ỉ': 'ỉ',
        'ẻ': 'ẻ', 'àk': u' à ','aˋ': 'à', 'iˋ': 'ì', 'ă´': 'ắ','ử': 'ử', 'e˜': 'ẽ', 'y˜': 'ỹ', 'a´': 'á',
        #Quy các icon về 2 loại emoj: Tích cực hoặc tiêu cực
        "👹": "tệ", "👻": "tốt", "💃": "tốt",'🤙': ' tốt ', '👍': ' tốt ',
        "💄": "tốt", "💎": "tốt", "💩": "tệ","😕": "tệ", "😱": "tệ", "😸": "tốt",
        "😾": "tệ", "🚫": "tệ",  "🤬": "tệ","🧚": "tốt", "🧡": "tốt",'🐶':' tốt ',
        '👎': ' tệ ', '😣': ' tệ ','✨': ' tốt ', '❣': ' tốt ','☀': ' tốt ',
        '♥': ' tốt ', '🤩': ' tốt ', 'like': ' tốt ', '💌': ' tốt ',
        '🤣': ' tốt ', '🖤': ' tốt ', '🤤': ' tốt ', ':(': ' tệ ', '😢': ' tệ ',
        '❤': ' tốt ', '😍': ' tốt ', '😘': ' tốt ', '😪': ' tệ ', '😊': ' tốt ',
        '?': ' ? ', '😁': ' tốt ', '💖': ' tốt ', '😟': ' tệ ', '😭': ' tệ ',
        '💯': ' tốt ', '💗': ' tốt ', '♡': ' tốt ', '💜': ' tốt ', '🤗': ' tốt ',
        '^^': ' tốt ', '😨': ' tệ ', '☺': ' tốt ', '💋': ' tốt ', '👌': ' tốt ',
        '😖': ' tệ ', '😀': ' tốt ', ':((': ' tệ ', '😡': ' tệ ', '😠': ' tệ ',
        '😒': ' tệ ', '🙂': ' tốt ', '😏': ' tệ ', '😝': ' tốt ', '😄': ' tốt ',
        '😙': ' tốt ', '😤': ' tệ ', '😎': ' tốt ', '😆': ' tốt ', '💚': ' tốt ',
        '✌': ' tốt ', '💕': ' tốt ', '😞': ' tệ ', '😓': ' tệ ', '️🆗️': ' tốt ',
        '😉': ' tốt ', '😂': ' tốt ', ':v': '  tốt ', '=))': '  tốt ', '😋': ' tốt ',
        '💓': ' tốt ', '😐': ' tệ ', ':3': ' tốt ', '😫': ' tệ ', '😥': ' tệ ',
        '😃': ' tốt ', '😬': ' 😬 ', '😌': ' 😌 ', '💛': ' tốt ', '🤝': ' tốt ', '🎈': ' tốt ',
        '😗': ' tốt ', '🤔': ' tệ ', '😑': ' tệ ', '🔥': ' tệ ', '🙏': ' tệ ',
        '🆗': ' tốt ', '😻': ' tốt ', '💙': ' tốt ', '💟': ' tốt ',
        '😚': ' tốt ', '❌': ' tệ ', '👏': ' tốt ', ';)': ' tốt ', '<3': ' tốt ',
        '🌝': ' tốt ',  '🌷': ' tốt ', '🌸': ' tốt ', '🌺': ' tốt ',
        '🌼': ' tốt ', '🍓': ' tốt ', '🐅': ' tốt ', '🐾': ' tốt ', '👉': ' tốt ',
        '💐': ' tốt ', '💞': ' tốt ', '💥': ' tốt ', '💪': ' tốt ',
        '💰': ' tốt ',  '😇': ' tốt ', '😛': ' tốt ', '😜': ' tốt ',
        '🙃': ' tốt ', '🤑': ' tốt ', '🤪': ' tốt ','☹': ' tệ ',  '💀': ' tệ ',
        '😔': ' tệ ', '😧': ' tệ ', '😩': ' tệ ', '😰': ' tệ ', '😳': ' tệ ',
        '😵': ' tệ ', '😶': ' tệ ', '🙁': ' tệ ',' 😅':'tốt','😌':'tốt',' 😅':'tốt',' 🆕':'',
        #Chuẩn hóa 1 số sentiment words/English words
        ':))': u'  tốt ', ':)': ' tốt ', 'ô kêi': ' ok ', 'okie': ' ok ', ' o kê ': ' ok ',
        'okey': ' ok ', 'ôkê': ' ok ', 'oki': ' ok ', ' oke ':  ' ok ',' okay':' ok ','okê':' ok ','☘':u'may mắn','✔':'được',
        ' tks ': u' cám ơn ', 'thks': u' cám ơn ', 'thanks': u' cám ơn ', 'ths': u' cám ơn ', 'thank': u' cám ơn ',
        '⭐': 'star ', '*': 'star ', '🌟': 'star ', '🎉': u' tốt ','☎':'điện thoại',' ͟ ':'','😴':'buồn ngủ','—':'','✅':'được',
        'kg ': u' không ','not': u' không ', u' kg ': u' không ', '"k ': u' không ',' kh ':u' không ','kô':u' không ','hok':u' không ',' kp ': u' không phải ',u' kô ': u' không ', '"ko ': u' không ', u' ko ': u' không ', u' k ': u' không ', 'khong': u' không ', u' hok ': u' không ',
        'he he': ' tốt ','hehe': ' tốt ','hihi': ' tốt ', 'haha': ' tốt ', 'hjhj': ' tốt ','—':'','⛵':'','🆘':u'khẩn cấp',
        ' lol ': u' tệ ',' cc ': u' tệ ','cute': u' dễ thương ','huhu': u' tệ ', ' vs ': u' với ', 'wa': ' quá ', 'wá': u' quá', 'j': u' gì ', '“': ' ',
        ' sz ': u' cỡ ', 'size': u' cỡ ', u' đx ': u' được ', 'dk': u' được ', 'dc': u' được ', 'đk': u' được ','1k':'tiền',
        'đc': u' được ','authentic': u' chuẩn chính hãng ',u' aut ': u' chuẩn chính hãng ', u' auth ': u' chuẩn chính hãng ', 'thick': u' tốt ', 'store': u' cửa hàng ',
        'shop': u' cửa hàng ', 'sp': u' sản phẩm ', 'gud': u' tốt ','god': u' tốt ','wel done':' tốt ', 'good': u' tốt ', 'gút': u' tốt ',
        'sấu': u' xấu ','gut': u' tốt ', u' tot ': u' tốt ', u' nice ': u' tốt ', 'perfect': 'rất tốt', 'bt': u' bình thường ',
        'time': u' thời gian ', 'qá': u' quá ', u' ship ': u' giao hàng ', u' m ': u' mình ', u' mik ': u' mình ',
        'ể': 'ể', 'product': 'sản phẩm', 'quality': 'chất lượng','chat':' chất ', 'excelent': 'hoàn hảo', 'bad': 'tệ','fresh': ' tươi ','sad': ' tệ ',
        'date': u' hạn sử dụng ', 'hsd': u' hạn sử dụng ','quickly': u' nhanh ', 'quick': u' nhanh ','fast': u' nhanh ','delivery': u' giao hàng ',u' síp ': u' giao hàng ',
        'beautiful': u' đẹp tuyệt vời ', u' tl ': u' trả lời ', u' r ': u' rồi ', u' shopE ': u' cửa hàng ',u' order ': u' đặt hàng ',' xd' : u'tốt',
        'chất lg': u' chất lượng ',u' sd ': u' sử dụng ',u' dt ': u' điện thoại ',u' nt ': u' nhắn tin ',u' tl ': u' trả lời ',u' sài ': u' xài ',u'bjo':u' bao giờ ',
        'thik': u' thích ',u' sop ': u' cửa hàng ', ' fb ': ' facebook ', ' face ': ' facebook ', ' very ': u' rất ',u'quả ng ':u' quảng  ','bh':u'bây giờ',
        'dep': u' đẹp ',u' xau ': u' xấu ','delicious': u' ngon ', u'hàg': u' hàng ', u'qủa': u' quả ',' cam on ':u' cảm ơn',' camon ':u' cảm ơn ',
        'iu': u' yêu ','fake': u' giả mạo ', 'trl': 'trả lời', '><': u' tốt ','clip':u'phim','mk':u'mình','tv':u'ti vi',
        ' por ': u' tệ ',' poor ': u' tệ ', 'ib':u' nhắn tin ', 'rep':u' trả lời ',u'fback':' feedback ','fedback':' feedback ','tks':u'cảm ơn','haiz':u'tệ',
        ' vcl ':u'tệ ', ' url ':' ','!':' ','post ':u'bài đăng ','shared ':'chia sẻ ','photo ':u'ảnh ',' 🏯 ':' ','z ':u'vậy ','new':u'mới',
        ' video ':u'phim',' ace ':u'anh chị em', ' a ':u'anh', ' inbox ':u'nhắn tin','🤦':u'tệ','feeling ':u'cảm thấy ','ak ':'à ','with ':'với ','live':u'trực tiếp',
        '▶ ':u'tiếp theo ','⭕':'','⚠ ':u'cảnh báo ','✈ ':u'máy bay ','củ ':u'giá tiền ','check ':u'kiểm tra ','review ':u'đánh giá ','format':u'bố cục','gb':u' ghi ','laptop': u'máy tính', ' v ':u' vậy',
        ' qtrong ':u'quan trọng ','soda ':u'nước uống ','camera':u'máy ảnh',' fanpage ':u'trang',' page ':'trang',' sory ':u'xin lỗi','ntn': u'như thế nào',
        ' sorry ':'xin lỗi ',' 😈 ':u'tệ',' hix ':'tệ',' max ':u'lớn nhất',' min ':u' nhỏ nhất ','link':u'địa chỉ','mp3':u'nhạc','tphcm':u'sài gòn',
        'vl':u'cực kì','his':u'của anh ấy','status':u'trạng thái','uploaded ':u'đã tải lên ','sl ':u'số lượng ',' sđt ':u'số điện thoại ',' star ':u'sao','cm':u'độ dài',' very ':u' rất ',
        ' to ':u'đến ','group ':u'nhóm ',' the ':' ','sick ':u' ốm ','😹 ':u'tốt ',' maps ':u'bản đồ  ','00usd':u'tiền','k':u' tiền ',' ak ':u' à ',' 😅':u' tốt ',
        ' chanel ': u'kênh ',' hotline ':u'điện thoại ',' loz ':u'tệ ','❓ ':' ',' e ':u' em ','00k ':u'tiền ','0k ':u'tiền ','5k':u' tiền ','kg':u' cân nặng ',
        ' exhausted ':u'tệ',' livestream ':u'trực tiếp',' live ':u'trực tiếp','♻':'',' marketing ':'tiếp thị ',' tp ':u'thành phố ',' 😲 ':'tốt ','world':u'thế giới',
        'url':'','   ': ' ','    ':' ','photos ':u'ảnh','s_post ':u'bài đăng ','feling':u'cảm thấy','crazy ':u'điên ','is':'',
        '➤':'','•':'','lyric':u'lời',' from':u' từ','sg ':u'sài gòn ','ful':u'đầy đủ','đm':u'tệ','cconcerned ':u'cân nhắc','post':u' bài đăng ','xl':u'xin lỗi',
        'set ':u'bộ ','♧ ':'','girls':u'gái','details':u'chi tiết','❗':'','▶':'',' online ': u'trực tuyến','❓':'','drama':u'chuyện',' relaxed':u'tốt','tired':u'tệ',
        'frustrated':u'tệ','group':u'nhóm','cty':'công ty','vđ':u'tệ','best':u'nhất','bos':'sếp','➡':'','up':u'đăng','others':u'khác','from':u'từ',
        '☄':'','coments':u'bình luận','comments':u'bình luận','fãi':u'phải','‼':'','website':u'trang','fanpage':u'trang','photos':u'ảnh',
        'style':u'phong cách','uploaded':u'đăng ','file':u'tệp',' faceboo ':u' mạng xã hội ',' facebook ':u' mạng xã hội ','and':u'và',
        'item':u'mặt hàng','sale':u'giảm giá','congratulation':u'chúc mừng','inb':u'nhắn tin','smartphone':u'điện thoại', 
        #dưới 3* quy về 1*, trên 3* quy về 5*
        '6 sao': u'5 sao ',
        'starstarstarstarstar': ' 5 sao ', '1 sao': ' 1star ', '1sao': ' 1star ','2 sao':' 1 sao ','2sao':' 1 sao ',
        '2 starstar':' 1 sao ', '0 sao': ' 1 sao ', '0star': ' 1 sao ',}

    for k, v in replace_list.items():
        text = text.replace(k, v)

    # chuyen punctuation thành space
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    text = text.translate(translator)
    #tokennize 
    text = ViTokenizer.tokenize(text)
    #xoa tu trung lap trong cau 
    text = re.sub("\s\s+", " ",text)
    text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)
    return text
  def predict(self, input):
    text = self.normalize_text(input)
    indexed = [int(self.vocab[token]) if token in self.vocab.keys() else 0 for token in text]
    tensor = torch.LongTensor(indexed).unsqueeze(0)
    label = int(torch.argmax(self.model(tensor),dim = 1).numpy().item())
    return label



