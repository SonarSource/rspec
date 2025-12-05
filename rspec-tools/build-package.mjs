import {readdirSync, readFileSync, existsSync, writeFileSync, mkdirSync, rmSync} from "node:fs";
import {join} from "node:path";
import createASCIIDoctor from "asciidoctor";

const asciiDoctor = createASCIIDoctor();

/**
 * @typedef BaseRuleRepresentation
 */

/**
 * @typedef RuleRepresentation
 * @property {string} title
 */

/**
 * @typedef Metadata
 * @property {string} documentation
 */

/**
 * @typedef Rule
 * @property {string} name
 * @property {string} language
 * @property {string} title
 * @property {string} type
 * @property {Metadata} metadata
 */

/**
 * @param {string} directoryPath
 * @return {Array<{
 *     rule: Rule;
 *     metadata: Metadata;
 * }>}
 */
const readDirectory = (directoryPath) => {
    const entries = readdirSync(directoryPath);

    /**
     * @param {string} rulePath
     * @param {string} name
     * @return {Array<{
     *     rule: Rule;
     *     metadata: Metadata;
     * }>}
     */
    const processRulePath = (rulePath, name) => {
        /**
         * @type {BaseRuleRepresentation}
         */
        const baseRuleRepresentation = JSON.parse(readFileSync(join(rulePath, 'metadata.json'), "utf-8"));

        const languageEntries = readdirSync(join(rulePath), {
            withFileTypes: true
        });

        /**
         * @type {Array<Rule>}
         */
        const results = [];

        languageEntries.forEach((languageEntry) => {
            if (languageEntry.isDirectory() && languageEntry.name === "javascript") {
                const languagePath = join(rulePath, languageEntry.name);
                const metadataPath = join(languagePath, 'metadata.json');

                if (existsSync(metadataPath)) {
                    /**
                     * @type {RuleRepresentation}
                     */
                    const ruleRepresentation = {
                        ...baseRuleRepresentation,
                        ...JSON.parse(readFileSync(metadataPath, "utf-8"))
                    };

                    const documentationPath = join(languagePath, 'rule.adoc');

                    /**
                     * @type {string}
                     */
                    let documentation;

                    if (existsSync(documentationPath)) {
                        documentation = readFileSync(documentationPath, "utf-8");

                        documentation = asciiDoctor.convert(documentation, {
                            base_dir: languagePath,
                            safe: 0
                        });
                    }

                    results.push({
                        rule: {
                            name,
                            language: languageEntry.name,
                            ...ruleRepresentation
                        },
                        metadata: {
                            documentation
                        }
                    });
                }
            }
        });

        return results;
    };

    const results = [];

    entries.forEach((entry) => {
        const rulePath = join(directoryPath, entry);

        results.push(...processRulePath(rulePath, entry));
    });

    return results;
};

const rules = readDirectory('rules');

const moduleContent = `const registry = new Map([
    ${rules.map((rule) => {
        return `['${rule.rule.language}/${rule.rule.name}', ${JSON.stringify(rule)}]`       
})}
]);

export const getRules = () => {
    return [...registry.values()].map((entry) => entry.rule);
};

export const getMetadata = (rule) => {
    const entry = registry.get(rule.language + '/' + rule.name);
    
    return entry.metadata;
};
`;

rmSync('build', {
    force: true,
    recursive: true
});

mkdirSync('build', {});

writeFileSync('build/index.mjs', moduleContent, {});

writeFileSync('build/index.d.ts', `export type Metadata = { 
    readonly documentation: string;
};
export type Rule = {
    readonly language: string;
    readonly name: string;
    readonly title: string;
    readonly type: string;
    readonly defaultQualityProfiles: Array<string>;
    readonly status: "ready" | "deprecated" | "closed";
};

export declare const getRules: () => Array<Rule>;
export declare const getMetadata: (rule: Rule) => Metadata;
`, {});

writeFileSync('build/package.json', JSON.stringify({
    main: "index.mjs",
    types: "index.d.ts",
    name: "@sonar/rspec",
    version: process.env.VERSION || "SNAPSHOT"
}));