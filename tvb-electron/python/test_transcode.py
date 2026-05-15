#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to simulate TVB progress output for Electron integration.
Outputs JSON progress messages to stdout.
"""

import json
import time
import sys

def output_json(data):
    print(json.dumps(data), flush=True)

def main():
    # Signal ready
    output_json({"type": "ready", "version": "1.0.1", "appname": "TVB Test"})
    
    # Simulate processing files
    total_files = 5
    for i in range(1, total_files + 1):
        # Start file
        output_json({
            "type": "progress",
            "progress": (i-1)/total_files * 100,
            "current": i,
            "total": total_files,
            "filename": f"movie{i}.mkv",
            "status": "processing"
        })
        
        # Simulate per-file progress
        for pct in [0, 25, 50, 75, 100]:
            output_json({
                "type": "progress",
                "progress": ((i-1) + pct/100) / total_files * 100,
                "current": i,
                "total": total_files,
                "filename": f"movie{i}.mkv",
                "status": "processing",
                "file_progress": pct
            })
            time.sleep(0.5)
        
        # Complete file
        output_json({
            "type": "complete",
            "filename": f"movie{i}.mkv",
            "success": True,
            "message": "Encoded successfully"
        })
    
    # Signal all done
    output_json({"type": "complete", "filename": "", "success": True, "message": "All files processed"})

if __name__ == "__main__":
    main()
