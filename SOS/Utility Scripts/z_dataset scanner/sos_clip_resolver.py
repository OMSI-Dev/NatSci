"""
SOS Clip Resolver
Helper functions to resolve clip names to dataset info using the cache.

This module provides fast lookups for clip information without needing to
know which theme folder a dataset is in.
"""

from __future__ import print_function
import json
import os


class ClipResolver:
    """
    Fast lookup for clip/dataset information from the cache.
    """
    
    def __init__(self, cache_file):
        """
        Initialize resolver with cache file.
        
        Args:
            cache_file: Path to dataset_cache.json
        """
        self.cache_file = cache_file
        self.datasets = {}
        self.loaded = False
        
        self.load_cache()
    
    def load_cache(self):
        """Load the dataset cache."""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            self.datasets = cache_data.get('datasets', {})
            self.loaded = True
            
            print("Clip resolver loaded: {0} datasets".format(len(self.datasets)))
            return True
            
        except Exception as e:
            print("ERROR: Could not load cache file: {0}".format(e))
            return False
    
    def get_clip_info(self, clip_name):
        """
        Get full information for a clip/dataset.
        Handles fuzzy matching for names like "Moon Phases" vs "moon_phases"
        
        Args:
            clip_name: Name of the clip (dataset name from SOS)
            
        Returns:
            dict with keys: is_movie, theme, path, srt_files, srt_path, video_files, has_captions
            Returns None if not found
        """
        if not self.loaded:
            return None
        
        # Try exact match first
        if clip_name in self.datasets:
            return self.datasets[clip_name]
        
        # Try normalized version (lowercase, spaces instead of underscores)
        normalized = clip_name.lower().replace('_', ' ').replace('-', ' ')
        if normalized in self.datasets:
            return self.datasets[normalized]
        
        # Try with underscores
        with_underscores = clip_name.lower().replace(' ', '_').replace('-', '_')
        if with_underscores in self.datasets:
            return self.datasets[with_underscores]
        
        # Try case-insensitive exact match
        for key in self.datasets.keys():
            if key.lower() == clip_name.lower():
                return self.datasets[key]
        
        return None
    
    def is_movie(self, clip_name):
        """Check if clip is a movie."""
        info = self.get_clip_info(clip_name)
        return info.get('is_movie', False) if info else False
    
    def has_captions(self, clip_name):
        """Check if clip has .srt captions."""
        info = self.get_clip_info(clip_name)
        return info.get('has_captions', False) if info else False
    
    def get_theme(self, clip_name):
        """Get the theme folder for a clip."""
        info = self.get_clip_info(clip_name)
        return info.get('theme') if info else None
    
    def get_srt_path(self, clip_name):
        """Get the full path to the .srt file."""
        info = self.get_clip_info(clip_name)
        return info.get('srt_path') if info else None
    
    def get_full_path(self, clip_name):
        """Get the full path to the dataset folder."""
        info = self.get_clip_info(clip_name)
        return info.get('path') if info else None
    
    def load_srt_content(self, clip_name):
        """
        Load and return the .srt file content.
        
        Args:
            clip_name: Name of the clip
            
        Returns:
            str: SRT file content, or None if not found
        """
        srt_path = self.get_srt_path(clip_name)
        
        if not srt_path or not os.path.exists(srt_path):
            return None
        
        try:
            with open(srt_path, 'r') as f:
                return f.read()
        except Exception as e:
            print("ERROR reading SRT: {0}".format(e))
            return None
    
    def print_clip_info(self, clip_name):
        """Print detailed information about a clip."""
        info = self.get_clip_info(clip_name)
        
        if not info:
            print("Clip '{0}' not found in cache".format(clip_name))
            return
        
        print("\n" + "=" * 60)
        print("Clip: {0}".format(clip_name))
        print("=" * 60)
        print("Theme:        {0}".format(info['theme']))
        print("Is Movie:     {0}".format('Yes' if info['is_movie'] else 'No'))
        print("Has Captions: {0}".format('Yes' if info['has_captions'] else 'No'))
        print("Path:         {0}".format(info['path']))
        
        if info['video_files']:
            print("Video Files:  {0}".format(', '.join(info['video_files'])))
        
        if info['srt_files']:
            print("SRT Files:    {0}".format(', '.join(info['srt_files'])))
            print("SRT Path:     {0}".format(info['srt_path']))
        
        print("=" * 60)


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sos_clip_resolver.py <cache_file> [clip_name]")
        print("\nExample:")
        print("  python sos_clip_resolver.py dataset_cache.json")
        print("  python sos_clip_resolver.py dataset_cache.json Aquaculture")
        sys.exit(1)
    
    cache_file = sys.argv[1]
    
    # Initialize resolver
    resolver = ClipResolver(cache_file)
    
    if not resolver.loaded:
        print("Failed to load cache file")
        sys.exit(1)
    
    # If clip name provided, look it up
    if len(sys.argv) >= 3:
        clip_name = sys.argv[2]
        resolver.print_clip_info(clip_name)
        
        # Try to load SRT
        if resolver.has_captions(clip_name):
            print("\nSRT Content Preview:")
            print("-" * 60)
            srt_content = resolver.load_srt_content(clip_name)
            if srt_content:
                # Show first 500 characters
                print(srt_content[:500])
                if len(srt_content) > 500:
                    print("... ({0} more characters)".format(len(srt_content) - 500))
    else:
        # Show some stats
        print("\nCache Statistics:")
        print("-" * 60)
        
        all_clips = resolver.datasets.keys()
        movies = [c for c in all_clips if resolver.is_movie(c)]
        movies_with_captions = [c for c in movies if resolver.has_captions(c)]
        
        print("Total clips:          {0}".format(len(all_clips)))
        print("Movies:               {0}".format(len(movies)))
        print("Movies with captions: {0}".format(len(movies_with_captions)))
        
        # Show themes
        themes = set(resolver.get_theme(c) for c in all_clips)
        print("Themes:               {0}".format(', '.join(sorted(themes))))
        
        print("\nExample movie clips with captions:")
        print("-" * 60)
        for clip in sorted(movies_with_captions)[:10]:
            theme = resolver.get_theme(clip)
            print("  [{0:12s}] {1}".format(theme, clip))
