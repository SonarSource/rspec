import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import Typography from '@material-ui/core/Typography';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Box from '@material-ui/core/Box';
import { createMuiTheme, Link, ThemeProvider } from '@material-ui/core';
import Highlight from 'react-highlight';
import { Link as RouterLink, useHistory } from 'react-router-dom';
import { RULE_STATE, useRuleCoverage } from './utils/useRuleCoverage';
import { useFetch } from './utils/useFetch';
import { RuleMetadata } from './types';
import parse, { attributesToProps, domToReact, DOMNode, Element } from 'html-react-parser';

import './hljs-humanoid-light.css';

const PARAMETER_INTERNAL_MARGIN = 0.5;

const useStyles = makeStyles((theme) => ({
  '@global': {
    h1: {
      fontSize: '1.6rem',
      fontWeight: 500,
      marginTop: theme.spacing(3),
      marginBottom: theme.spacing(3)
    },
    h2: {
      color: '#0B3C62',
      fontSize: '1.2rem'
    },
    h3: {
      fontSize: '1rem',
      color: '#25699D'
    },
    hr: {
      color: '#F9F9FB'
    },
    '.sidebarblock': {
      '& .title': {
        marginTop: theme.spacing(2),
        color: '#25699D'
      },
      '& pre': {
        marginLeft: '1rem',
        marginTop: theme.spacing(PARAMETER_INTERNAL_MARGIN),
        marginBottom: theme.spacing(PARAMETER_INTERNAL_MARGIN)
      },
      '& p': {
        marginLeft: '1rem',
        marginTop: theme.spacing(PARAMETER_INTERNAL_MARGIN),
        marginBottom: theme.spacing(PARAMETER_INTERNAL_MARGIN)
      }
    }
  },
  ruleBar: {
    borderBottom: '1px solid lightgrey',
  },
  ruleid: {
    textAlign: 'center',
    marginTop: theme.spacing(3),
    marginBottom: theme.spacing(3),
    color: 'black'
  },
  ruleidLink: {
    color: 'inherit',
  },
  title: {
    textAlign: 'justify',
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(4),
  },
  avoid: {
    textDecoration: 'line-through'
  },
  coverage: {
    marginBottom: theme.spacing(3),
  },
  description: {
    textAlign: 'justify',
    // marginBottom: theme.spacing(3),
  },

  // style used to center the tabs when there too few of them to fill the container
  tabRoot: {
    justifyContent: 'center'
  },
  tabScroller: {
    flexGrow: 0
  },
  unimplemented: {
    color: 'red'
  },

  tab: {
    display: 'flex',

    '&::before': {
      content: '""',
      display: 'block',
      width: theme.spacing(1),
      height: theme.spacing(1),
      marginRight: theme.spacing(1),
      borderRadius: theme.spacing(1),
    },

    '& > .MuiTab-wrapper': {
      width: 'auto',
    }
  },
  coveredTab: {
    '&::before': {
      backgroundColor: RULE_STATE['covered'].color,
    }
  },
  targetedTab: {
    '&::before': {
      borderColor: RULE_STATE['targeted'].color,
      border: '1px solid',
      backgroundColor: 'transparent'
    }
  },
  removedTab: {
    '&::before': {
      backgroundColor: RULE_STATE['removed'].color,
    }
  },
  closedTab: {
    '&::before': {
      backgroundColor: RULE_STATE['closed'].color,
    }
  },
  deprecatedTab: {
    '&::before': {
      backgroundColor: RULE_STATE['deprecated'].color,
    }
  },
}));

const theme = createMuiTheme({});

type UsedStyles = ReturnType<typeof useStyles>;

const languageToJiraProject = new Map(Object.entries({
  'PYTHON': 'SONARPY',
  'ABAP': 'SONARABAP',
  'AZURERESOURCEMANAGER': 'SONARIAC',
  'CFAMILY': 'CPP',
  'DOCKER': 'SONARIAC',
  'JAVA': 'SONARJAVA',
  'COBOL': 'SONARCOBOL',
  'FLEX': 'SONARFLEX',
  'HTML': 'SONARHTML',
  'PHP': 'SONARPHP',
  'PLI': 'SONARPLI',
  'PLSQL': 'SONARPLSQL',
  'RPG': 'SONARRPG',
  'APEX': 'SONARSLANG',
  'RUBY': 'SONARSLANG',
  'KOTLIN': 'SONARKT',
  'SCALA': 'SONARSLANG',
  'GO': 'SONARSLANG',
  'SECRETS': 'SECRETS',
  'SWIFT': 'SONARSWIFT',
  'TSQL': 'SONARTSQL',
  'VB6': 'SONARVBSIX',
  'XML': 'SONARXML',
  'CLOUDFORMATION': 'SONARIAC',
  'TERRAFORM': 'SONARIAC',
  'KUBERNETES': 'SONARIAC',
  'TEXT': 'SONARTEXT',
}));

const languageToGithubProject = new Map(Object.entries({
  'ABAP': 'sonar-abap',
  'AZURERESOURCEMANAGER': 'sonar-iac',
  'CSHARP': 'sonar-dotnet',
  'DOCKER': 'sonar-iac',
  'VBNET': 'sonar-dotnet',
  'JAVASCRIPT': 'SonarJS',
  'TYPESCRIPT': 'SonarJS',
  'SWIFT': 'sonar-swift',
  'KOTLIN': 'sonar-kotlin',
  'GO': 'slang-enterprise',
  'SCALA': 'slang-enterprise',
  'RUBY': 'slang-enterprise',
  'APEX': 'slang-enterprise',
  'HTML': 'sonar-html',
  'COBOL': 'sonar-cobol',
  'VB6': 'sonar-vb',
  'JAVA': 'sonar-java',
  'PLI': 'sonar-pli',
  'CFAMILY': 'sonar-cpp',
  'CSS': 'sonar-css',
  'FLEX': 'sonar-flex',
  'PHP': 'sonar-php',
  'PLSQL': 'sonar-plsql',
  'PYTHON': 'sonar-python',
  'RPG': 'sonar-rpg',
  'TSQL': 'sonar-tsql',
  'XML': 'sonar-xml',
  'CLOUDFORMATION': 'sonar-iac',
  'TERRAFORM': 'sonar-iac',
  'KUBERNETES': 'sonar-iac',
  'SECRETS': 'sonar-secrets',
  'TEXT': 'sonar-text',
}));

function ticketsAndImplementationPRsLinks(ruleNumber: string, title: string, language?: string) {
  if (language) {
    const upperCaseLanguage = language.toUpperCase();
    const jiraProject = languageToJiraProject.get(upperCaseLanguage);
    const githubProject = languageToGithubProject.get(upperCaseLanguage);
    const titleWihoutQuotes = title.replace(/"/g, "'");

    const implementationPRsLink = (
      <Link href={`https://github.com/SonarSource/${githubProject}/pulls?q=is%3Apr+"S${ruleNumber}"+OR+"RSPEC-${ruleNumber}"`}>
        Implementation Pull Requests
      </Link>
    );

    if (jiraProject !== undefined) {
      const ticketsLink = (
        <Link href={`https://jira.sonarsource.com/issues/?jql=project%20%3D%20${jiraProject}%20AND%20(text%20~%20%22S${ruleNumber}%22%20OR%20text%20~%20%22RSPEC-${ruleNumber}%22%20OR%20text%20~%20"${titleWihoutQuotes}")`}>
          Implementation tickets on Jira
        </Link>
      );
      return {ticketsLink, implementationPRsLink};
    } else {
      const ticketsLink = (
        <Link href={`https://github.com/SonarSource/${githubProject}/issues?q=is%3Aissue+"S${ruleNumber}"+OR+"RSPEC-${ruleNumber}"`}>
          Implementation issues on GitHub
        </Link>
      );
      return {ticketsLink, implementationPRsLink};
    }
  } else {
    const ticketsLink = (<div>Select a language to see the implementation tickets</div>);
    const implementationPRsLink = (<div>Select a language to see the implementation pull requests</div>);
    return {ticketsLink, implementationPRsLink};
  }
}

function RuleThemeProvider({ children }: any) {
  useStyles();
  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}

interface PageMetadata {
  title: string;
  languagesTabs: JSX.Element[] | null;
  avoid: boolean;
  prUrl: string | undefined;
  branch: string;
  coverage: any;
  jsonString: string | undefined;
}

function usePageMetadata(ruleid: string, language: string, classes: UsedStyles): PageMetadata {
  const metadataUrl = `${process.env.PUBLIC_URL}/rules/${ruleid}/${language ?? 'default'}-metadata.json`;
  let [metadataJSON, metadataError, metadataIsLoading] = useFetch<RuleMetadata>(metadataUrl);

  let coverage: any = 'Loading...';
  let title = 'Loading...';
  let avoid = false;
  let metadataJSONString;
  let languagesTabs = null;
  let prUrl: string | undefined = undefined;
  let branch = 'master';
  const { ruleCoverage, allLangsRuleCoverage, ruleStateInAnalyzer } = useRuleCoverage();
  if (metadataJSON && !metadataIsLoading && !metadataError) {
    title = metadataJSON.title;
    if ('prUrl' in metadataJSON) {
      prUrl = metadataJSON.prUrl;
    }
    branch = metadataJSON.branch;
    metadataJSON.languagesSupport.sort((a, b) => a.name.localeCompare(b.name));
    const ruleStates = metadataJSON.languagesSupport.map(({ name, status }) => ({
      name,
      ruleState: ruleStateInAnalyzer(name, metadataJSON!.allKeys, status)
    }));
    languagesTabs = ruleStates.map(({ name, ruleState }) => {
      const classNames = classes.tab + ' ' + (classes as any)[ruleState + 'Tab'];
      return <Tab key={name} label={name} value={name} className={classNames} />;
    });
    avoid = !ruleStates.some(({ ruleState }) => ruleState === 'covered' || ruleState === 'targeted');
    metadataJSONString = JSON.stringify(metadataJSON, null, 2);

    const coverageMapper = (key: any, range: any) => {
      if (typeof range === 'string') {
        return (
          <li key={key} >{key}: {range}</li>
        );
      } else {
        return (
          <li>Not covered for {key} anymore. Was covered from {range['since']} to {range['until']}.</li>
        );
      }
    };
    if (language) {
      coverage = ruleCoverage(language, metadataJSON.allKeys, coverageMapper);
    } else {
      coverage = allLangsRuleCoverage(metadataJSON.allKeys, coverageMapper);
    }
  }

  if (coverage !== 'Not Covered') {
    prUrl = undefined;
    branch = 'master'; 
  }

  return {
    title,
    languagesTabs,
    avoid,
    prUrl,
    branch,
    coverage,
    jsonString: metadataJSONString
  };
}

function getRspecPath(rspecId: string, language?: string) {
  return '/rspec#/rspec/' + rspecId;
}

function useDescription(metadata: PageMetadata, ruleid: string, language?: string) {
  const editOnGithubUrl =
    `https://github.com/SonarSource/rspec/blob/${metadata.branch}/rules/${ruleid}${language ? '/' + language : ''}`;

  function htmlReplacement(domNode: Element) {
    if (domNode.name === 'a' && domNode.attribs && domNode.attribs['data-rspec-id']) {
      const props = attributesToProps(domNode.attribs);
      return <a href={getRspecPath(domNode.attribs['data-rspec-id'], language)} {...props}>
        {domToReact(domNode.children)}
      </a>;
    }

    if (domNode.name === 'code' && domNode.attribs && domNode.attribs['data-lang']) {
      return <Highlight className={domNode.attribs['data-lang']}>
        {domToReact(domNode.children)}
      </Highlight>;
    }

    return undefined; // No modification.
  }

  const descUrl = `${process.env.PUBLIC_URL}/rules/${ruleid}/${language ?? 'default'}-description.html`;

  const [descHTML, descError, descIsLoading] = useFetch<string>(descUrl, false);

  if (descHTML !== null && !descIsLoading && !descError) {
    return <div>
      {parse(descHTML, { replace: (d: DOMNode) => htmlReplacement(d as Element) })}
      <hr />
      <a href={editOnGithubUrl}>Edit on Github</a><br />
      <hr />
      <Highlight className='json'>{metadata.jsonString}</Highlight>
    </div>;
  }
  return <div>Loading...</div>;
}

export function RulePage(props: any) {
  // language can be absent
  const {ruleid, language} = props.match.params;
  document.title = ruleid;

  const history = useHistory();
  function handleLanguageChange(event: any, lang: string) {
    history.push(`/${ruleid}/${lang}`);
  }

  const classes = useStyles();

  const metadata = usePageMetadata(ruleid, language, classes);
  const description = useDescription(metadata, ruleid, language);

  let prLink = <></>;
  if (metadata.prUrl) {
    prLink = <div>
      <span className={classes.unimplemented}>Not implemented (see <a href={metadata.prUrl}>PR</a>)</span>
    </div>;
  }
  const ruleNumber = ruleid.substring(1);

  const specificationPRsLink = (
    <Link href={`https://github.com/SonarSource/rspec/pulls?q=is%3Apr+"S${ruleNumber}"+OR+"RSPEC-${ruleNumber}"`}>
      Specification Pull Requests
    </Link>
  );

  const {ticketsLink, implementationPRsLink} = ticketsAndImplementationPRsLinks(ruleNumber, metadata.title, language);
  const tabsValue = language ? {'value' : language} : {'value': false};

  return (
    <div>
      <div className={classes.ruleBar}>
        <Container>
          <Typography variant="h2" classes={{ root: classes.ruleid }}>
            <Link className={`${classes.ruleidLink} ${metadata.avoid ? classes.avoid : ''}`}
                component={RouterLink} to={`/${ruleid}`} underline="none">{ruleid}</Link>
          </Typography>
          <Typography variant="h4" classes={{ root: classes.ruleid }}>{prLink}</Typography>
          <Tabs
            {...tabsValue}
            onChange={handleLanguageChange}
            indicatorColor="primary"
            textColor="primary"
            variant="scrollable"
            scrollButtons="auto"
            classes={{ root: classes.tabRoot, scroller: classes.tabScroller }}
          >
            {metadata.languagesTabs}
          </Tabs>
        </Container>
      </div>

      <RuleThemeProvider>
        <Container maxWidth="md">
          <h1>{metadata.title}</h1>
          <hr />
          <Box className={classes.coverage}>
            <h2>Covered Since</h2>
            <ul>
              {metadata.coverage}
            </ul>
          </Box>

          <Box className={classes.coverage}>
            <h2>Related Tickets and Pull Requests</h2>
            <ul>
              {specificationPRsLink}
            </ul>
            <ul>
              {implementationPRsLink}
            </ul>
            <ul>
              {ticketsLink}
            </ul>
          </Box>

          <Box>
            <Typography component={'span'} className={classes.description}>
              {description}
            </Typography>
          </Box>
        </Container>
      </RuleThemeProvider>
    </div>
  );
}
