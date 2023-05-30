package org.sonarsource.rspec;

import java.util.List;
import org.sonar.api.SonarRuntime;
import org.sonar.api.server.rule.RulesDefinition;
import org.sonarsource.analyzer.commons.RuleMetadataLoader;

public class RspecShowcaseRulesDefinition implements RulesDefinition {

  public static final String REPOSITORY_KEY = "rspec-showcase";
  public static final String RESOURCE_FOLDER = "org/sonar/l10n/rspec/rules/";

  public static final String PROFILE_PATH =
    RESOURCE_FOLDER + REPOSITORY_KEY + "/Sonar_way_profile.json";

  private final SonarRuntime sonarRuntime;

  public RspecShowcaseRulesDefinition(SonarRuntime sonarRuntime) {
    this.sonarRuntime = sonarRuntime;
  }
  @Override
  public void define(Context context) {
    var repo = context.createRepository(REPOSITORY_KEY, "java")
      .setName("RSPEC Showcase");

    RuleMetadataLoader ruleMetadataLoader = new RuleMetadataLoader(
      RESOURCE_FOLDER + REPOSITORY_KEY,
      PROFILE_PATH,
      sonarRuntime
    );

    ruleMetadataLoader.addRulesByRuleKey(repo, List.of("S6620"));

    repo.done();
  }
}
