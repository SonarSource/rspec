import fs from 'fs';
import path from 'path';
import { withDir } from 'tmp-promise';

/**
 * Creates a file hierarchy in the given parent directory.
 * @param parentDirectory directory in which the files will be created.
 * @param files files to create.
 */
export function createFiles(parentDirectory: string, files: Record<string, string>) {
  for (const [slashPath, content] of Object.entries(files)) {
    const splitFilePath = slashPath.split('/');

    const dirPath = path.join(parentDirectory, ...splitFilePath.slice(0, -1));
    fs.mkdirSync(dirPath, {recursive: true});

    const filePath = path.join(parentDirectory, ...splitFilePath)
    fs.writeFileSync(filePath, content);
  }
}

/**
 * Create a temporary directory which will be deleted when callback's promise resolve.
 * @param callback callback to call while the mock directories exist.
 */
export function withTestDir(callback: (path: string) => Promise<unknown>) {
  return withDir((dir) => {
    return callback(dir.path);
  }, { unsafeCleanup: true });
}