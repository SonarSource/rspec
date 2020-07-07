const fs = require('fs');
const path = require('path');
const asciidoctor = require("asciidoctor")();
const stripHtml = require("string-strip-html");
const lunr = require('lunr');

const RULE_SRC_DIRECTORY = path.join("..", "rules");
const RULE_DST_DIRECTORY = path.join("public", "rules");

function clean_rules() {
    console.log("Deleting rules."); 
    fs.rmdirSync(RULE_DST_DIRECTORY, { recursive: true });
}

function generate_rules_metadata_and_description() {
    const ruleIndexStore = {};
    fs.mkdirSync(RULE_DST_DIRECTORY, { recursive: true });
    fs.readdirSync(RULE_SRC_DIRECTORY).forEach(fileName => {
        const ruleSrcDirectory = path.join(RULE_SRC_DIRECTORY, fileName);
        const ruleDstDirectory = path.join(RULE_DST_DIRECTORY, fileName);
        try {
            generate_rule_metadata_and_description(ruleSrcDirectory, ruleDstDirectory, ruleIndexStore);
        } catch (e) {
            console.error("ERROR while generating " + fileName + ": " + e);
        }
    });
    const ruleIndexJson = JSON.stringify(build_search_index(ruleIndexStore));
    fs.writeFileSync(path.join(RULE_DST_DIRECTORY, "rule-index.json"), ruleIndexJson, {encoding: 'utf8'});
    // Remove the descriptions as they are only interesting for indexing
    for (const rule of Object.values(ruleIndexStore)) {
        delete rule.descriptions;
    }
    const ruleIndexStoreJson = JSON.stringify(ruleIndexStore, null, 2);
    fs.writeFileSync(path.join(RULE_DST_DIRECTORY, "rule-index-store.json"), ruleIndexStoreJson, {encoding: 'utf8'});
}

function generate_rule_metadata_and_description(/*string*/ruleSrcDirectory, /*string*/ruleDstDirectory, ruleIndexStore) {
    const all_languages = findSupportedLanguage(ruleSrcDirectory);
    // Search records will be indexed by lunr search engine
    const ruleKey = parseInt(ruleSrcDirectory.split('/').pop().substring(1))
    const searchRecord = {
        id: ruleKey,
        languages: all_languages,
        type: null,
        defaultSeverity: null,
        titles: new Set(),
        tags: new Set(),
        qualityProfiles: new Set(),
        descriptions: new Set(),
    }
    ruleIndexStore[ruleKey] = (searchRecord);

    console.log("Converting '" + ruleSrcDirectory + "' into '" + ruleDstDirectory + "' for languages: " + all_languages.join(", "));
    all_languages.forEach(language => {
        fs.mkdirSync(ruleDstDirectory, { recursive: true });
        const htmlDescription = generate_rule_description(ruleSrcDirectory, ruleDstDirectory, language);
        const metadata = generate_rule_metadata(ruleSrcDirectory, ruleDstDirectory, language, all_languages);

        // populate the search record
        searchRecord.titles.add(metadata.title);
        searchRecord.type = metadata.type;
        searchRecord.defaultSeverity = metadata.defaultSeverity;
        if (metadata.tags) {
            for (const tag of metadata.tags.values()) {
                searchRecord.tags.add(tag);
            }
        }
        if (metadata.qualityProfiles) {
            for (const qualityProfile of metadata.qualityProfiles.values()) {
                searchRecord.qualityProfiles.add(qualityProfile);
            }
        }
        // Remove HTML tags from the description, extract unique words and normalize them.
        // This reduces a bit the footprint of descriptions in the index.
        descriptionWords = stripHtml(htmlDescription).split(/[\s,.:;!?()"'-+*/\\%#]+/)
        descriptionWords.forEach(item => searchRecord.descriptions.add(item.toUpperCase()));
    });

    // replace Set with lists so that it can be used with JSON.stringify
    searchRecord.titles = Array.from(searchRecord.titles).join('\n');
    searchRecord.descriptions = Array.from(searchRecord.descriptions).join(' ');
    searchRecord.tags = Array.from(searchRecord.tags);
    searchRecord.qualityProfiles = Array.from(searchRecord.qualityProfiles);
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
    return html;
}

function generate_rule_metadata(ruleSrcDirectory, ruleDstDirectory, language, all_languages) {
    let parentFile = path.join(ruleSrcDirectory, language, "metadata.json");
    const parentJson = fs.existsSync(parentFile) ? JSON.parse(fs.readFileSync(parentFile, 'utf8')) : {};
    let childFile = path.join(ruleSrcDirectory, "metadata.json");
    const childJson = fs.existsSync(childFile) ? JSON.parse(fs.readFileSync(childFile, 'utf8')) : {};
    const mergedJson = {...childJson, ...parentJson};
    mergedJson["all_languages"] = all_languages;
    const dstJsonFile = path.join(ruleDstDirectory, language + "-metadata.json");
    fs.writeFileSync(dstJsonFile, JSON.stringify(mergedJson, null, 2), {encoding: 'utf8'});
    return mergedJson;
}

function build_search_index(ruleIndexStore) {
    function selectivePipeline(token) {
        const fields = token.metadata["fields"];
        // process only titles and descriptions
        if (fields.includes('titles') || fields.includes('descriptions') ) {
            // We don't use the stopword filter to allow words such as "do", "while", "for"
            const trimmed = lunr.trimmer(token);
            return lunr.stemmer(trimmed);
        }
        return token;        
    }
    lunr.Pipeline.registerFunction(selectivePipeline, 'selectivePipeline');

    var ruleIndex = lunr(function () {
        // Set our own token processing pipeline
        this.pipeline.reset();
        this.pipeline.add(selectivePipeline);

        this.ref('id');
        this.field('titles');
        this.field('type');
        this.field('defaultSeverity');
        this.field('tags');
        this.field('qualityProfiles');
        this.field('descriptions');


        for (const searchRecord of Object.values(ruleIndexStore)) {
            this.add(searchRecord);
        }
    })

    return ruleIndex;
}

function findSupportedLanguage(/*string*/ruleDirectory) /*string[]*/ {
    return fs.readdirSync(ruleDirectory)
      .filter(fileName => fs.lstatSync(path.join(ruleDirectory, fileName)).isDirectory())
      .sort();
}

function fileExtension(/*string*/language) /*string*/ {
    return language === "cobol" ? "cbl" : language;
}

clean_rules()
generate_rules_metadata_and_description()
