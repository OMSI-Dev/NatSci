"""
Metadata Cache Module
Handles caching of SOS dataset metadata to minimize server queries.
"""

import os
import json
import hashlib


class MetadataCache:
    """Cache manager for SOS dataset metadata."""
    
    def __init__(self, cache_dir=None):
        """
        Initialize metadata cache.
        
        Args:
            cache_dir: Directory for cache storage (defaults to 'metadata_cache' in script dir)
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), 'metadata_cache')
        
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # In-memory cache for fast lookups
        self.memory_cache = {}
        
        # Track which clips are in cache
        self.cached_clips = set()
        
        # Load existing cache index
        self._load_cache_index()
    
    def _get_cache_filepath(self, clip_name):
        """
        Get filepath for cached metadata file.
        
        Args:
            clip_name: Name of the clip
            
        Returns:
            str: Path to cache file
        """
        # Sanitize filename - replace invalid characters
        safe_name = "".join(c if c.isalnum() or c in ('-', '_', ' ') else '_' for c in clip_name)
        safe_name = safe_name[:200]  # Limit filename length
        
        # Use hash to ensure uniqueness for long names
        name_hash = hashlib.md5(clip_name.encode('utf-8')).hexdigest()[:8]
        filename = f"{safe_name}_{name_hash}.json"
        
        return os.path.join(self.cache_dir, filename)
    
    def _load_cache_index(self):
        """Load cache index to know which clips are cached."""
        index_path = os.path.join(self.cache_dir, '_cache_index.json')
        
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                    self.cached_clips = set(index_data.get('clips', []))
                print(f"[Metadata Cache] Loaded index with {len(self.cached_clips)} cached clips")
            except Exception as e:
                print(f"[Metadata Cache] Warning: Could not load cache index: {e}")
                self.cached_clips = set()
        else:
            print("[Metadata Cache] No existing cache index found - will build new cache")
    
    def _save_cache_index(self):
        """Save cache index."""
        index_path = os.path.join(self.cache_dir, '_cache_index.json')
        
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump({'clips': list(self.cached_clips)}, f, indent=2)
        except Exception as e:
            print(f"[Metadata Cache] Warning: Could not save cache index: {e}")
    
    def has_clip(self, clip_name):
        """
        Check if clip metadata is in cache.
        
        Args:
            clip_name: Name of the clip
            
        Returns:
            bool: True if cached, False otherwise
        """
        return clip_name in self.cached_clips
    
    def get(self, clip_name):
        """
        Get metadata for a clip from cache.
        
        Args:
            clip_name: Name of the clip
            
        Returns:
            dict: Metadata dictionary, or None if not cached
        """
        # Check memory cache first
        if clip_name in self.memory_cache:
            return self.memory_cache[clip_name]
        
        # Check disk cache
        if not self.has_clip(clip_name):
            return None
        
        cache_path = self._get_cache_filepath(clip_name)
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Store in memory cache for fast future access
            self.memory_cache[clip_name] = metadata
            return metadata
            
        except Exception as e:
            print(f"[Metadata Cache] Warning: Could not load cached metadata for '{clip_name}': {e}")
            # Remove from index if file is corrupted
            self.cached_clips.discard(clip_name)
            self._save_cache_index()
            return None
    
    def set(self, clip_name, metadata):
        """
        Save metadata for a clip to cache.
        
        Args:
            clip_name: Name of the clip
            metadata: Metadata dictionary to cache
        """
        cache_path = self._get_cache_filepath(clip_name)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Update memory cache and index
            self.memory_cache[clip_name] = metadata
            self.cached_clips.add(clip_name)
            self._save_cache_index()
            
        except Exception as e:
            print(f"[Metadata Cache] Warning: Could not save metadata for '{clip_name}': {e}")
    
    def get_batch(self, clip_names):
        """
        Get metadata for multiple clips.
        
        Args:
            clip_names: List of clip names
            
        Returns:
            dict: Dictionary mapping clip_name -> metadata (only for cached clips)
        """
        results = {}
        for clip_name in clip_names:
            metadata = self.get(clip_name)
            if metadata is not None:
                results[clip_name] = metadata
        return results
    
    def set_batch(self, metadata_dict):
        """
        Save metadata for multiple clips.
        
        Args:
            metadata_dict: Dictionary mapping clip_name -> metadata
        """
        for clip_name, metadata in metadata_dict.items():
            self.set(clip_name, metadata)
    
    def clear(self):
        """Clear all cached metadata."""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)
            self.memory_cache.clear()
            self.cached_clips.clear()
            self._save_cache_index()
            print("[Metadata Cache] Cache cleared")
        except Exception as e:
            print(f"[Metadata Cache] Warning: Could not clear cache: {e}")
    
    def get_stats(self):
        """
        Get cache statistics.
        
        Returns:
            dict: Statistics about the cache
        """
        return {
            'total_cached_clips': len(self.cached_clips),
            'memory_cached_clips': len(self.memory_cache),
            'cache_dir': self.cache_dir
        }
