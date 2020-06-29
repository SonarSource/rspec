const fs = require('fs');
const path = require('path');
const asciidoctor = require("asciidoctor")();

const RULE_SRC_DIRECTORY = path.join("..", "rules");
const RULE_DST_DIRECTORY = path.join("build", "static", "generated", "rules");

function generate_rules_metadata_and_description() {
    const ruleIndex = {};
    fs.mkdirSync(RULE_DST_DIRECTORY, { recursive: true });
    fs.readdirSync(RULE_SRC_DIRECTORY).forEach(fileName => {
        const ruleSrcDirectory = path.join(RULE_SRC_DIRECTORY, fileName);
        const ruleDstDirectory = path.join(RULE_DST_DIRECTORY, fileName);
        try {
            generate_rule_metadata_and_description(ruleSrcDirectory, ruleDstDirectory, ruleIndex);
        } catch (e) {
            console.error("ERROR while generating " + fileName + ": " + e);
        }
    });
    const ruleIndexJson = JSON.stringify(ruleIndex, null, 2);
    fs.writeFileSync(path.join(RULE_DST_DIRECTORY, "rule-index.json"), ruleIndexJson, {encoding: 'utf8'});
    fs.writeFileSync(path.join(RULE_DST_DIRECTORY, "rule-index.js"), "const RULE_INDEX = " + ruleIndexJson + ";", {encoding: 'utf8'});
}

function generate_rule_metadata_and_description(/*string*/ruleSrcDirectory, /*string*/ruleDstDirectory, /*object*/ruleIndex) {
    const languages = findSupportedLanguage(ruleSrcDirectory);
    ruleIndex[path.basename(ruleSrcDirectory)] = languages;
    console.log("Converting '" + ruleSrcDirectory + "' into '" + ruleDstDirectory + "' for languages: " + languages.join(", "));
    languages.forEach(language => {
        fs.mkdirSync(ruleDstDirectory, { recursive: true });
        generate_rule_metadata(ruleSrcDirectory, ruleDstDirectory, language);
        generate_rule_description(ruleSrcDirectory, ruleDstDirectory, language);
    });
}

function generate_rule_description(ruleSrcDirectory, ruleDstDirectory, language) {
    let ruleSrcFile = path.join(ruleSrcDirectory, language, "rule.adoc");
    if (!fs.existsSync(ruleSrcFile)) {
        ruleSrcFile = path.join(ruleSrcDirectory, "rule.adoc");
        if (!fs.existsSync(ruleSrcFile)) {
            throw new Error("Missing file 'rule.adoc' for language '" + language + " in " + ruleSrcDirectory);
        }
    }
    const ruleDstFile = path.join(ruleDstDirectory, language + "-description.html");
    const baseDir = path.resolve(path.dirname(ruleSrcFile));
    const opts = {
        safe: 'unsafe',
        base_dir: baseDir,
        attributes: {
            language: language,
            language_group: language,
            file_extension: fileExtension(language)
        }
    };
    const adoc = fs.readFileSync(ruleSrcFile, 'utf8');
    const html = /** @type string*/ asciidoctor.convert(adoc, opts);
    fs.writeFileSync(ruleDstFile, html, {encoding: 'utf8'});
}

function generate_rule_metadata(ruleSrcDirectory, ruleDstDirectory, language) {
    let parentFile = path.join(ruleSrcDirectory, language, "metadata.json");
    const parentJson = fs.existsSync(parentFile) ? JSON.parse(fs.readFileSync(parentFile, 'utf8')) : {};
    let childFile = path.join(ruleSrcDirectory, "metadata.json");
    const childJson = fs.existsSync(childFile) ? JSON.parse(fs.readFileSync(childFile, 'utf8')) : {};
    const mergedJson = {...parentJson, ...childJson};
    const dstJsonFile = path.join(ruleDstDirectory, language + "-metadata.json");
    fs.writeFileSync(dstJsonFile, JSON.stringify(mergedJson, null, 2), {encoding: 'utf8'});
}

function findSupportedLanguage(/*string*/ruleDirectory) /*string[]*/ {
    return fs.readdirSync(ruleDirectory)
      .filter(fileName => fs.lstatSync(path.join(ruleDirectory, fileName)).isDirectory())
      .sort();
}

function fileExtension(/*string*/language) /*string*/ {
    return language === "cobol" ? "cbl" : language;
}

generate_rules_metadata_and_description()
