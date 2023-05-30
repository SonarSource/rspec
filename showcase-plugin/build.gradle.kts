import com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar
import org.gradle.internal.impldep.com.google.gson.GsonBuilder
import java.nio.file.Files
import java.nio.file.Path
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter


plugins {
    id("java")
    id("com.github.johnrengelman.shadow") version "8.1.1"
}

group = "org.sonarsource.rspec"
version = "1.0-SNAPSHOT"

// The environment variables ARTIFACTORY_PRIVATE_USERNAME and ARTIFACTORY_PRIVATE_PASSWORD are used on CI env (Azure)
// On local box, please add artifactoryUsername and artifactoryPassword to ~/.gradle/gradle.properties
val artifactoryUsername = System.getenv("ARTIFACTORY_PRIVATE_READER_USERNAME")
    ?: (if (project.hasProperty("artifactoryUsername")) project.property("artifactoryUsername").toString() else "")
val artifactoryPassword = System.getenv("ARTIFACTORY_PRIVATE_READER_PASSWORD")
    ?: (if (project.hasProperty("artifactoryPassword")) project.property("artifactoryPassword").toString() else "")

repositories {
    mavenCentral {
        content {
            excludeGroupByRegex("com\\.sonarsource.*")
        }
    }
    maven("https://repox.jfrog.io/repox/sonarsource") {
        if (artifactoryUsername.isNotEmpty() && artifactoryPassword.isNotEmpty()) {
            credentials {
                username = artifactoryUsername
                password = artifactoryPassword
            }
        }
    }
}

val ruleMetadata by configurations.creating {
    isTransitive = false
}

dependencies {
    compileOnly("org.sonarsource.api.plugin:sonar-plugin-api:9.17.0.587")
    implementation("org.sonarsource.analyzer-commons:sonar-analyzer-commons:2.5.0.1358")
    testImplementation(platform("org.junit:junit-bom:5.9.1"))
    testImplementation("org.junit.jupiter:junit-jupiter")

    ruleMetadata("com.sonarsource.rule-api:rule-api:2.6.0.2454")
}

tasks.test {
    useJUnitPlatform()
}

tasks {
    named<ShadowJar>("shadowJar") {
        archiveClassifier.set("")

        val formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssZ")
        val formattedDate = OffsetDateTime.now().format(formatter)

        manifest {
            attributes(mapOf(
                "Main-Class" to "com.github.csolem.gradle.shadow.kotlin.example.App",
                "Plugin-Key" to "rspec-showcase",
                "Plugin-Version" to project.version,
                "Plugin-Class" to "org.sonarsource.rspec.RspecShowcasePlugin",
                "Sonar-Version" to "9.9",
                "SonarLint-Supported" to "true",
                "Plugin-Name" to "Showcase plugin for RSPEC",
                "Plugin-Description" to "Demonstrate all supported features in rule descriptions",
                "Plugin-License" to "SonarSource",
                "Plugin-BuildDate" to formattedDate,
            ))
        }
    }
}

tasks {
    build {
        dependsOn(shadowJar)
    }
}

task("generateRuleMetadata", JavaExec::class) {
    group = "ruleApi"
    classpath = ruleMetadata
    args = listOf("generate", "-rule", "S6620", "-branch", "rule/add-RSPEC-S6620")
}

