from .. import DB

# ###Constants####

BITS_PER_NIBBLE = 4

# ###Configurable####

HASH_SIZE = 16 # Must be a power of 2
CHARACTERS_PER_CHUNK = 2 # Must be a power of 2

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


## RENAME THIS TO SimilarityData
class SimilarityResult(DB.Model):
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
    ratio = DB.Column(DB.Float, nullable=True)
    
    chunk_columns = {}
    for i in range(0, NUM_CHUNKS):
        key = ChunkKey(i)
        chunk_columns[key] = DB.Column(DB.String(2), nullable=False)
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
    def cross_similarity_clause1(self, image_hash):
        clause = None
        # Left-Right, Forward-Down
        for i in range(0, NUM_CHUNKS):
            chunk1 = i
            chunk2 = (i + 1) % NUM_CHUNKS
            subclause = (getattr(self, ChunkKey(chunk1)) == HexChunk(image_hash, chunk1)) & \
                        (getattr(self, ChunkKey(chunk2)) == HexChunk(image_hash, chunk2))
            groupclause = subclause.self_group()
            clause = clause | groupclause if clause is not None else groupclause
        # Backward-Down
        for i in range(0, NUM_CHUNKS//2):
            chunk1 = i * 2
            chunk2 = (chunk1 + 3) % NUM_CHUNKS
            subclause = (getattr(self, ChunkKey(chunk1)) == HexChunk(image_hash, chunk1)) & \
                        (getattr(self, ChunkKey(chunk2)) == HexChunk(image_hash, chunk2))
            groupclause = subclause.self_group()
            clause |= groupclause
        return clause

    @classmethod
    def cross_similarity_clause2(self, image_hash):
        #subclause = (self.chunk00 == HexChunk(image_hash, 0))
        #subclause &= (getattr(self, ChunkKey(NUM_CHUNKS-1)) == HexChunk(image_hash, NUM_CHUNKS - 1))
        #clause = subclause.self_group()
        clause = None
        for i in range(0, NUM_CHUNKS-1): #Need to check if fixing this makes it worse
            if i % 2 == 0:
                chunk1 = i
                chunk2 = (i + 3) % NUM_CHUNKS
                chunk3 = (i + 4) % NUM_CHUNKS
                chunk4 = (i + 7) % NUM_CHUNKS
            else:
                chunk1 = i
                chunk2 = (i + 1) % NUM_CHUNKS
                chunk3 = (i + 4) % NUM_CHUNKS
                chunk4 = (i + 5) % NUM_CHUNKS
            subclause = (getattr(self, ChunkKey(chunk1)) == HexChunk(image_hash, chunk1)) & \
                        (getattr(self, ChunkKey(chunk2)) == HexChunk(image_hash, chunk2)) & \
                        (getattr(self, ChunkKey(chunk3)) == HexChunk(image_hash, chunk3)) # & \
                        #(getattr(self, ChunkKey(chunk4)) == HexChunk(image_hash, chunk4))
            groupclause = subclause.self_group()
            clause = clause | groupclause if clause is not None else groupclause
        return clause