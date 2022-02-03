import fs from 'fs';
import os from 'os';
import path from 'path';
import { Location, createMemoryHistory } from 'history';
import { render } from '@testing-library/react';
import { Router } from 'react-router-dom';

import { generateRulesDescription } from '../deployment/description';
import { generateRulesMetadata } from '../deployment/metadata';
import { createIndexFiles } from '../deployment/searchIndex';
import { createFiles } from '../deployment/testutils';
import { fetchMock, normalize, FetchResult } from '../testutils';
import { SearchPage } from '../SearchPage';

// The CI system is a bit slow. Increase timeout to avoid random failures.
jest.setTimeout(20000);

function readJson(filepath: string) {
  const content = fs.readFileSync(filepath);
  return JSON.parse(content.toString());
}

const Paths = {
  src: '',
  dst: '',
  index: '',
  store: '',
  aggregates: '',
};

beforeAll(() => {
  Paths.src = fs.mkdtempSync(path.join(os.tmpdir(), 'end-to-end-testing-src-'));
  Paths.dst = fs.mkdtempSync(path.join(os.tmpdir(), 'end-to-end-testing-dst-'));

  createFiles(Paths.src, {
    'S100/rule.adoc': 'Generic content',
    'S100/metadata.json': JSON.stringify({
      title: 'Generic Rule S100 Title',
      tags: ['confusing'],
      type: 'CODE_SMELL',
      defaultQualityProfiles: [
        'Sonar way'
      ],
    }),
    'S100/java/rule.adoc': 'Java Content',
    'S100/java/metadata.json': JSON.stringify({
      title: 'Java Rule S100 Title',
      status: 'ready',
    }),

    'S200/rule.adoc': 'Generic content',
    'S200/metadata.json': JSON.stringify({
      title: 'Generic Rule S200 Title',
      tags: ['confusing'],
      type: 'CODE_SMELL',
    }),
    'S200/python/rule.adoc': 'Python content',
    'S200/python/metadata.json': JSON.stringify({
      title: 'Python Rule S200 Title',
      tags: ['pep8'],
      status: 'ready',
    }),
    'S200/java/rule.adoc': 'Java Content',
    'S200/java/metadata.json': JSON.stringify({
      title: 'Java Rule S200 Title',
      type: 'BUG',
      status: 'ready',
    }),

    'S501/rule.adoc': 'Generic content, no active language',
    'S501/metadata.json': JSON.stringify({
      title: 'Rule S501 Rule is closed with no language-specific specification',
      type: 'CODE_SMELL',
      status: 'closed',
    }),
  });

  generateRulesMetadata(Paths.src, Paths.dst);
  generateRulesDescription(Paths.src, Paths.dst);
  createIndexFiles(Paths.dst);

  Paths.index = path.join(Paths.dst, 'rule-index.json');
  Paths.store = path.join(Paths.dst, 'rule-index-store.json');
  Paths.aggregates = path.join(Paths.dst, 'rule-index-aggregates.json');
  expect(fs.existsSync(Paths.index)).toBeTruthy();
  expect(fs.existsSync(Paths.store)).toBeTruthy();
  expect(fs.existsSync(Paths.aggregates)).toBeTruthy();
});

afterAll(() => {
  // FIXME replace with fs.rm(path, { recursive: true, force: true }) when upgrading node to 14.14 or later.
  fs.rmdirSync(Paths.dst, { recursive: true });
  fs.rmdirSync(Paths.src, { recursive: true });
});

beforeEach(() => {
  const index = readJson(Paths.index);
  const indexStore = readJson(Paths.store);
  const indexAggregates = readJson(Paths.aggregates);

  const rootUrl = process.env.PUBLIC_URL;
  const mockUrls = {} as Record<string, FetchResult>;
  mockUrls[`${rootUrl}/rules/rule-index.json`] = { json: normalize(index) };
  mockUrls[`${rootUrl}/rules/rule-index-store.json`] = { json: normalize(indexStore) };
  mockUrls[`${rootUrl}/rules/rule-index-aggregates.json`] = { json: normalize(indexAggregates) };
  mockUrls[`${rootUrl}/covered_rules.json`] = {
    json: {
      'JAVA': { 'S100': 'ver1', 'S200': 'ver2' },
      'PY': { 'S200': 'ver1' },
    }
  };
  jest.spyOn(global, 'fetch').mockImplementation(fetchMock(mockUrls));
});

afterEach(() => {
  (global.fetch as any).mockClear();
});

const defaultUseLocation = jest.requireActual('react-router-dom').useLocation;
let fakeLocation: Location | undefined = undefined;

function mockUseLocation() {
  return fakeLocation ?? defaultUseLocation();
}

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom') as {},
  useLocation: mockUseLocation,
}));

beforeEach(() => {
  fakeLocation = undefined;
});

function generateFakeLocation(search: string): Location {
  return {
    pathname: '/somepath',
    search: search,
    state: null,
    hash: 'somehash',
    key: undefined,
  };
}

const history = createMemoryHistory();
beforeAll(() => {
  history.push('/rspec/#/rspec/');
});

describe('The main search page display correct results', () => {

  test('Empty query', async () => {
    expect(fakeLocation).toBeUndefined();
    const { findByText, findAllByText } = render(<Router history={history} > <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 3\b/);
    await findByText(/Java Rule S100 Title/);
    await findByText(/Python Rule S200 Title/);
    await findByText(/Java Rule S200 Title/);
    await findByText(/Rule S501 Rule is closed with no language-specific specification/);
  });

  test('Query by title: Java.', async () => {
    fakeLocation = generateFakeLocation('query=Java');
    const { findByText, findAllByText } = render(<Router history={history}> <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 2/);
    await findByText(/Java Rule S100 Title/);
    await findByText(/Python Rule S200 Title/);
    await findByText(/Java Rule S200 Title/);
  });

  test('Query by title: S501.', async () => {
    fakeLocation = generateFakeLocation('query=S501');
    const { findByText, findAllByText } = render(<Router history={history}> <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 1/);
    await findByText(/Rule S501 Rule is closed with no language-specific specification/);
  });

  test('Query by type: BUG', async () => {
    fakeLocation = generateFakeLocation('types=BUG');
    const { findByText, findAllByText } = render(<Router history={history}> <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 1/);
    await findByText(/Java Rule S200 Title/);
  });

  test('Query by type: VULNERABILITY', async () => {
    fakeLocation = generateFakeLocation('types=VULNERABILITY');
    const { findByText, findAllByText } = render(<Router history={history}> <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 0/);
  });

  test('Query by tag: confusing', async () => {
    fakeLocation = generateFakeLocation('tags=confusing');
    const { findByText, findAllByText } = render(<Router history={history}> <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 2/);
    await findByText(/Java Rule S100 Title/);
    await findByText(/Java Rule S200 Title/);
    await findByText(/Python Rule S200 Title/);
  });

  test('Query by tag: confusing & pep8', async () => {
    fakeLocation = generateFakeLocation('tags=confusing,pep8');
    const { findByText, findAllByText } = render(<Router history={history}> <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 1/);
    await findByText(/Python Rule S200 Title/);
  });

  test('Query by language: python', async () => {
    fakeLocation = generateFakeLocation('lang=python');
    const { findByText, findAllByText } = render(<Router history={history}> <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 1/);
    await findByText(/Python Rule S200 Title/);
  });

  test('Advanced query', async () => {
    fakeLocation = generateFakeLocation('qualityProfiles=Sonar way&query=Java&tags=confusing');
    const { findByText, findAllByText } = render(<Router history={history}> <SearchPage /></Router >);
    expect(await findAllByText(/Rule Title and Description/)).toHaveLength(1 + 1); // <label> + <span>
    await findByText(/Number of rules found: 1/);
    await findByText(/Java Rule S100 Title/);
  });

});
