from sortedcontainers import SortedDict

class TrieNode:
    def __init__(self):
        self.ends = False
        self.children = SortedDict()

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.suggested_words = []
        self.suggested_word_limit = 10
        self.potential_word = [] # list of chars for efficiency

    def load_values(self, words=[]):
        for word in words:
            self.add(word)

    def add(self, word=''):
        current_node = self.root
        for ch in word:
            current_node = current_node.children.setdefault(ch, TrieNode())
        
        current_node.ends = True


    def remove(self, word=''):
        current_node = self.root
        for ch in word:
            if not ch in current_node.children:
                return
            current_node = current_node.children[ch]

        current_node.ends = False

    def get_suggestions(self, prefix=''):
        current_node = self.root
        for ch in prefix:
            if not ch in current_node.children:
                return []
            current_node = current_node.children[ch]
        self.suggested_words = []
        self.potential_word = [prefix]
        self._get_suggestions_recursive(current_node)
        return self.suggested_words
        
    def _get_suggestions_recursive(self, node):
        if len(self.suggested_words) >= self.suggested_word_limit:
            return
        if node.ends:
            self.suggested_words.append(''.join(self.potential_word))
        for ch, child in node.children.items():
            self.potential_word.append(ch)
            self._get_suggestions_recursive(child)
            self.potential_word.pop()


    def clear(self):
        self.root.children = SortedDict()
