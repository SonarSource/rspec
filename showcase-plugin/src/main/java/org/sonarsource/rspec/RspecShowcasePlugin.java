package org.sonarsource.rspec;

import org.sonar.api.Plugin;

public class RspecShowcasePlugin implements Plugin {
  @Override
  public void define(Context context) {
    context.addExtension(RspecShowcaseRulesDefinition.class);
  }
}
