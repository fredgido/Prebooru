from .. import DB

# ###Constants####

BITS_PER_NIBBLE = 4

# ###Configurable####

HASH_SIZE = 16 # Must be a power of 2
CHARACTERS_PER_CHUNK = 1 # Must be a power of 2

# ###Calculated####

BITS_PER_CHUNK = CHARACTERS_PER_CHUNK * BITS_PER_NIBBLE
NUM_CHUNKS = (HASH_SIZE * HASH_SIZE) // BITS_PER_CHUNK

def ChunkKey(index):
    return 'chunk' + str(index).zfill(2)

def ChunkIndex(index):
    return index * CHARACTERS_PER_CHUNK

def HexChunk(hashstr, index):
    strindex = ChunkIndex(index)
    return hashstr[strindex : strindex + CHARACTERS_PER_CHUNK]

def GetBoxIndexes(corner_index):
    box_indexes = []
    for i in range(8):
        row_index = corner_index + (i * 4)
        box_indexes.extend([row_index, row_index + 1])
    return box_indexes

def GetBoxIndexes2(corner_index):
    box_indexes = []
    for i in range(4):
        box_indexes.append(corner_index + i * 4)
    return box_indexes

def GetBoxIndexes3(corner_index):
    box_indexes = []
    for i in range(8):
        box_indexes.append(corner_index + i * 4)
    return box_indexes

def GetBoxIndexes4(corner_index):
    box_indexes = []
    for i in range(6):
        box_indexes.append(corner_index + i * 4)
    return box_indexes

class SimilarityResult3(DB.Model):
    __bind_key__ = 'similarity'
    
    @property
    def image_hash(self):
        rethash = ""
        for i in range(0, NUM_CHUNKS):
            rethash += getattr(self, ChunkKey(i))
        return rethash
    
    @image_hash.setter
    def image_hash(self, image_hash):
        for i in range(0, NUM_CHUNKS):
            setattr(self, ChunkKey(i), HexChunk(image_hash, i))
    
    id = DB.Column(DB.Integer, primary_key=True)
    post_id = DB.Column(DB.Integer, nullable=False)
    
    chunk_columns = {}
    for i in range(0, NUM_CHUNKS):
        key = ChunkKey(i)
        chunk_columns[key] = DB.Column(DB.String(CHARACTERS_PER_CHUNK), nullable=False)
    locals().update(chunk_columns)
    del chunk_columns, i, key
    
    @classmethod
    def similarity_clause(self, image_hash):
        clause = self.chunk00 == image_hash[0:2]
        for i in range(1, NUM_CHUNKS):
            clause |= (getattr(self, ChunkKey(i)) == HexChunk(image_hash, i))
        return clause
    
    @classmethod
    def cross_similarity_clause(self, image_hash):
        subclause = (self.chunk00 == HexChunk(image_hash, 0))
        subclause &= (getattr(self, ChunkKey(NUM_CHUNKS-1)) == HexChunk(image_hash, NUM_CHUNKS - 1))
        clause = subclause.self_group()
        for i in range(1, NUM_CHUNKS-1):
            subclause = (getattr(self, ChunkKey(i)) == HexChunk(image_hash, i)) & (getattr(self, ChunkKey(i+1)) == HexChunk(image_hash, i+1))
            clause |= subclause.self_group()
        return clause
    
    @classmethod
    def box_similarity_clause(self, image_hash):
        clause = None
        for i in range(9):
            for j in range(4):
                corner_index = (i * 4) + j
                box_indexes = GetBoxIndexes3(corner_index)
                print(box_indexes)
                subclause = None
                for k in box_indexes:
                    chunkclause = (getattr(self, ChunkKey(k)) == HexChunk(image_hash, k))
                    subclause = subclause & chunkclause if subclause is not None else chunkclause
                grouped_clause = subclause.self_group()
                clause = clause | grouped_clause if clause is not None else grouped_clause
        return clause
