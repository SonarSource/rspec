
import path from 'path';
import { render, waitFor, fireEvent, within } from '@testing-library/react';
import { SearchPage } from '../SearchPage';
import { buildIndexStore, buildSearchIndex } from '../deployment/searchIndex';
import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { fetchMockObject, normalize } from '../testutils';

// The CI system is a bit slow. Increase timeout to avoid random failures.
jest.setTimeout(20000);

function genMockUrls() {
    const rulePath = path.join(__dirname, '..', 'deployment', '__tests__', 'resources', 'metadata');
    const [indexStore, indexAggregates] = buildIndexStore(rulePath);
    const searchIndex: lunr.Index = buildSearchIndex(indexStore);
    const rootUrl = process.env.PUBLIC_URL;
    let mockUrls: {[index: string]: any} = {};
    mockUrls[`${rootUrl}/rules/rule-index.json`] = {json: normalize(searchIndex)};
    mockUrls[`${rootUrl}/rules/rule-index-store.json`] = {json: normalize(indexStore)};
    mockUrls[`${rootUrl}/rules/rule-index-aggregates.json`] = {json: normalize(indexAggregates)};
    mockUrls[`${rootUrl}/covered_rules.json`] = {json:
        {'CPP': {'S1000': 'ver1', 'S987': 'ver2', 'S3457': 'ver1'},
         'C': {'S1000': 'c1', 'S234': {'since': 'c2', 'until': 'c3'}},
         'PY': {'S3457': {'since': 'p2', 'until': 'p3'}}}
    };
    return mockUrls;
}

let fetchMocker = fetchMockObject(genMockUrls());

beforeEach(() => {
    jest.spyOn(global, 'fetch').mockImplementation(fetchMocker.mock as jest.Mocked<typeof fetch>);
});

afterEach(() => {
    fetchMocker.reset();
    global.fetch.mockClear();
});

async function renderDefaultSearchPageWithHistory() {
    const history = createMemoryHistory();
    history.push('/rspec/#/rspec/');
    const renderResult = render(<Router history={history}><SearchPage /></Router>);

    // Finish rendering after fetching all the data
    await waitFor(() => fetchMocker.finished());

    return {renderResult, history};
}

async function renderDefaultSearchPage() {
    const { renderResult } = await renderDefaultSearchPageWithHistory();

    expect(renderResult.queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(renderResult.queryByText(/rules found: 5/i)).not.toBeNull();
    return renderResult;
}

test('renders the list of all rules', async () => {
    const { findByText, asFragment } = await renderDefaultSearchPage();
    await findByText(/rules found/i);
    expect(asFragment()).toMatchSnapshot();
});

test('narrows search by title', async () => {
    const { queryByText, queryByTestId, getByRole } = await renderDefaultSearchPage();

    // Enter a search query
    const searchBox = getByRole('textbox');
    fireEvent.change(searchBox, { target: { value: 'should not be used' } });

    expect(queryByTestId('search-hit-S987')).not.toBeNull();
    expect(queryByTestId('search-hit-S1000')).toBeNull();
    expect(queryByTestId('search-hit-S1007')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();
    expect(queryByText(/rules found: 3/i)).not.toBeNull();
});

test('on enter navigates to the ruleid', async () => {
    const { renderResult: { getByRole }, history } = await renderDefaultSearchPageWithHistory();

    // Enter a search query
    const searchBox = getByRole('textbox');
    fireEvent.change(searchBox, { target: { value: 'S1000' } });
    fireEvent.keyUp(searchBox, { key: 'Enter', code: 'Enter', charCode: 13});

    await waitFor(() => fetchMocker.finished());
    expect(history.entries[history.entries.length - 1].pathname).toBe('/rspec/S1000');
});

test('on enter does not navigate to the wrong ruleid', async () => {
    const { renderResult: { getByRole }, history } = await renderDefaultSearchPageWithHistory();

    // Enter a search query
    const searchBox = getByRole('textbox');
    fireEvent.change(searchBox, { target: { value: 'S10000' } });
    fireEvent.keyUp(searchBox, { key: 'Enter', code: 'Enter', charCode: 13});

    await waitFor(() => fetchMocker.finished());
    expect(history.entries[history.entries.length - 1].pathname).toBe('/rspec/');
});

test('does nothing on keyup other than enter', async () => {
    const { renderResult: { getByRole }, history } = await renderDefaultSearchPageWithHistory();

    // Enter a search query
    const searchBox = getByRole('textbox');
    fireEvent.change(searchBox, { target: { value: 'S1000' } });
    fireEvent.keyUp(searchBox, { key: 'A', code: 'KeyA'});
    expect(history.entries[history.entries.length - 1].pathname).toBe('/rspec/');
});

test('on enter navigates to the singular result', async () => {
    const { renderResult: {queryByText, getByRole}, history } = await renderDefaultSearchPageWithHistory();

    // Enter a search query
    const searchBox = getByRole('textbox');
    fireEvent.change(searchBox, { target: { value: 'rather validated compiler' } });
    expect(queryByText(/rules found: 1/i)).not.toBeNull();
    fireEvent.keyUp(searchBox, { key: 'Enter', code: 'Enter', charCode: 13});

    await waitFor(() => fetchMocker.finished());
    expect(history.entries[history.entries.length - 1].pathname).toBe('/rspec/S3457');
});

test('shows the exact match first', async () => {
    const { queryByText, queryByTestId, getAllByTestId, getByRole } = await renderDefaultSearchPage();

    // Search for S1000
    const searchBox = getByRole('textbox');
    fireEvent.change(searchBox, { target: { value: 'S1000' } });

    expect(queryByText(/rules found: 2/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).toBeNull();
    // Make sure S1000 comes before S987
    let hitsS1000 = getAllByTestId(/search-hit/i).map((hit) => hit.getAttribute('data-testid'));
    expect(hitsS1000.indexOf('search-hit-S1000')).toBeLessThan(hitsS1000.indexOf('search-hit-S987'));

    // Search for S987
    fireEvent.change(searchBox, { target: { value: 'S987' } });

    expect(queryByText(/rules found: 2/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).toBeNull();
    // Make sure S987 comes before S1000
    let hitsS987 = getAllByTestId(/search-hit/i).map((hit) => hit.getAttribute('data-testid'));
    expect(hitsS987.indexOf('search-hit-S987')).toBeLessThan(hitsS987.indexOf('search-hit-S1000'));
});

test('narrows search by rule type', async () => {
    const { queryByText, queryByTestId, getByRole, getByTestId } = await renderDefaultSearchPage();

    // Select the rule type
    fireEvent.mouseDown(within(getByTestId('rule-type')).getByRole('button'));
    const listbox = within(getByRole('listbox'));
    fireEvent.click(listbox.getByTestId('rule-type-CODE_SMELL'));

    expect(queryByTestId('search-hit-S987')).toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S1007')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();
    expect(queryByText(/rules found: 3/i)).not.toBeNull();
});

test('narrows search by rule tags', async () => {
    const { queryByText, queryByTestId, getByRole, getByTestId } = await renderDefaultSearchPage();

    // Select the 'clumsy' tag
    fireEvent.mouseDown(within(getByTestId('rule-tags')).getByRole('button'));
    const listbox = within(getByRole('listbox'));
    fireEvent.click(listbox.getByTestId('rule-tag-clumsy'));
    expect(queryByText(/rules found: 2/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();

    // Also select the 'pitfall' tag
    fireEvent.click(listbox.getByTestId('rule-tag-pitfall'));
    expect(queryByText(/rules found: 1/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).toBeNull();
});

test('narrows search by language', async () => {
    const { queryByText, queryByTestId, getByRole, getByTestId } = await renderDefaultSearchPage();

    // Select the cfamily language, should keep all the rules: they all are specified for cfamily
    fireEvent.mouseDown(within(getByTestId('rule-language')).getByRole('button'));
    const listbox = within(getByRole('listbox'));
    fireEvent.click(listbox.getByTestId('rule-language-cfamily'));
    expect(queryByText(/rules found: 4/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).not.toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();

    // Select the java language: should keep only S3457
    fireEvent.click(listbox.getByTestId('rule-language-java'));
    expect(queryByText(/rules found: 2/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).toBeNull();
    expect(queryByTestId('search-hit-S1000')).toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();
});

test('narrows search by quality profile', async () => {
    const { queryByText, queryByTestId, getByRole, getByTestId } = await renderDefaultSearchPage();

    // Select Sonar way profile - S1000, S1007, S3457 and S3649 are in this profile
    fireEvent.mouseDown(within(getByTestId('rule-default-quality-profile')).getByRole('button'));
    const listbox = within(getByRole('listbox'));
    fireEvent.click(listbox.getByTestId('rule-qual-profile-Sonar way'));
    expect(queryByText(/rules found: 3/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();
});
