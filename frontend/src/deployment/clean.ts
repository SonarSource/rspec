import { RULE_DST_DIRECTORY } from './paths';
import fs from 'fs';

/**
 * Remove rules preprocessed for the fronted.
 */
export function clean_rules() {
    console.log("Deleting rules."); 
    fs.rmdirSync(RULE_DST_DIRECTORY, { recursive: true });
}