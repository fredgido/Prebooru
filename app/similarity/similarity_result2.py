from .. import DB

# ###Constants####

BITS_PER_NIBBLE = 4

# ###Configurable####

HASH_SIZE = 16 # Must be a power of 2
CHARACTERS_PER_CHUNK = 4 # Must be a power of 2

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

class SimilarityResult2(DB.Model):
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
        chunk_columns[key] = DB.Column(DB.String(2), nullable=False)
    locals().update(chunk_columns)
    del chunk_columns, i, key
    
    @classmethod
    def similarity_query(self, image_hash):
        clause = self.chunk00 == image_hash[0:2]
        for i in range(1, NUM_CHUNKS):
            clause |= (getattr(self, ChunkKey(i)) == HexChunk(image_hash, i))
        return clause
