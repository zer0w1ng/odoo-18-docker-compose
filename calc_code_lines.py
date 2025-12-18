import os
import argparse

# Define the file extensions to consider as code/text
# You can customize this set as needed.
CODE_EXTENSIONS = {
    # Common programming languages
    '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rb', '.php',
    '.swift', '.kt', '.scala', '.pl', '.pm', '.lua', '.r', '.dart',
    # Web development
    '.js', '.ts', '.jsx', '.tsx', '.html', '.htm', '.css', '.scss', '.less',
    '.vue', '.svelte',
    # Scripting
    '.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd',
    # Data and configuration
    '.xml', '.json', '.yaml', '.yml', '.ini', '.cfg', '.toml',
    # Documentation and text
    '.md', '.rst', '.txt', '.tex', '.log',
    # SQL
    '.sql',
    # Others
    '.csv', '.tsv',
}

def is_likely_text_file(filepath, block_size=512):
    """
    Tries to determine if a file is a text file by checking for null bytes
    and attempting a UTF-8 decode on a small block.
    """
    try:
        with open(filepath, 'rb') as f:
            block = f.read(block_size)
        if b'\0' in block:  # Null byte often indicates a binary file
            return False
        # Try decoding as UTF-8 as a further check
        block.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False  # Failed to decode as UTF-8, likely not plain text or different encoding
    except Exception:
        return False  # Other read errors

def count_lines_in_file(filepath):
    """
    Counts non-empty lines in a given file.
    Skips lines that are empty or contain only whitespace.
    """
    lines = 0
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # errors='ignore' helps with files containing occasional non-UTF-8 chars
            for line_content in f:
                if line_content.strip():  # Count only if the line has non-whitespace content
                    lines += 1
            return lines
    except Exception as e:
        print(f"  [Warning] Skipping file '{filepath}' due to error: {e}")
        return 0

def get_aggregation_key_dir(dirpath, root_dir):
    """
    Determines the aggregation key (the "2nd level directory") for a given dirpath
    relative to the root_dir.
    - Files in root_dir aggregate to root_dir.
    - Files in root_dir/subdir1/* aggregate to root_dir/subdir1.
    """
    # root_dir is already absolute from main()
    abs_dirpath = os.path.abspath(dirpath)

    if abs_dirpath == root_dir: # root_dir itself
        return root_dir

    try:
        # rel_path will be like 'subdir1' or 'subdir1/subdir2'
        rel_path = os.path.relpath(abs_dirpath, root_dir)
    except ValueError:
        # This case should ideally not be reached if dirpath is always under root_dir
        return abs_dirpath # Fallback

    path_parts = rel_path.split(os.sep)

    if not path_parts or path_parts[0] == '.' or path_parts[0] == '':
        # This case should also be covered by 'abs_dirpath == root_dir'
        return root_dir

    # Aggregation key is root_dir + first component of relative path
    return os.path.join(root_dir, path_parts[0])

def count_loc_in_directory(root_dir):
    """
    Counts lines of code for specified file types in a directory and its subdirectories.
    Returns a dictionary with "2nd level directory" paths as keys and aggregated line counts as values,
    and a grand total.
    """
    aggregated_dir_line_counts = {}
    grand_total_lines = 0

    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' not found.")
        return {}, 0

    for dirpath, _, filenames in os.walk(root_dir):
        current_dir_lines_for_walked_dir = 0 # Lines for the specific dirpath being walked
        # print(f"Processing directory: {dirpath}") # Uncomment for verbose progress

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            file_ext = os.path.splitext(filename)[1].lower()

            process_file = False
            if file_ext in CODE_EXTENSIONS:
                process_file = True
            elif not file_ext:  # For files without an extension
                if is_likely_text_file(filepath):
                    # print(f"  - Considering '{filename}' (no ext, likely text)") # Uncomment for verbose
                    process_file = True
                # else:
                    # print(f"  - Skipping '{filename}' (no ext, likely binary)") # Uncomment for verbose

            if process_file:
                lines_in_current_file = count_lines_in_file(filepath)
                if lines_in_current_file > 0:
                    # print(f"  - {filename}: {lines_in_current_file} lines") # Uncomment for verbose
                    current_dir_lines_for_walked_dir += lines_in_current_file

        if current_dir_lines_for_walked_dir > 0:
            aggregation_key = get_aggregation_key_dir(dirpath, root_dir)
            aggregated_dir_line_counts[aggregation_key] = \
                aggregated_dir_line_counts.get(aggregation_key, 0) + current_dir_lines_for_walked_dir
            grand_total_lines += current_dir_lines_for_walked_dir # Grand total sums all lines from all files

    return aggregated_dir_line_counts, grand_total_lines

def main():
    parser = argparse.ArgumentParser(
        description="Count non-empty lines of code in a directory for specified file types, "
                    "summarized per 2nd level directory."
    )
    parser.add_argument(
        "directory",
        help="The root directory to scan."
    )
    args = parser.parse_args()

    target_directory = os.path.abspath(args.directory) # Get absolute path

    print(f"Counting lines of code in: {target_directory}")
    print(f"Considering files with extensions: {', '.join(sorted(list(CODE_EXTENSIONS)))}")
    print("Also considering text files without extensions.\n")

    dir_counts, total_lines = count_loc_in_directory(target_directory)

    if dir_counts:
        print("Lines of code per 2nd level directory (non-empty lines):")
        # Sort directories for consistent and readable output
        for dir_path in sorted(dir_counts.keys()):
            print(f"  {dir_path}: {dir_counts[dir_path]} lines")
        print("\n-----------------------------------")
        print(f"Grand Total Lines of Code: {total_lines}")
    else:
        print("No matching files found or the directory is empty/contains no scannable files.")

if __name__ == "__main__":
    main()
