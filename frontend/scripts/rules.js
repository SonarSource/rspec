const asciidoc = require("asciidoctor")();

function build_rules_descriptions() {
    const result = asciidoc.convert("test");
    console.log(result);
    
}
build_rules_descriptions()
