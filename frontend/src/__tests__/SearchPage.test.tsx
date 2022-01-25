import React from 'react';
import path from 'path';
import { render, waitFor, fireEvent, within } from '@testing-library/react';
import { screen } from '@testing-library/dom';
import { SearchPage } from '../SearchPage';
import { buildIndexStore, buildSearchIndex } from '../deployment/searchIndex';
import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { fetchMockObject } from '../testutils';

function normalize(obj) {
    // Lunr (the search engine) expects its objects to have been
    // serialized and deserialized when it is queried.
    // This is not a no-op, because, for example, it translates function references to
    // simple labels on the serialization step, and then uses these labels to
    // restore the function references when loading.
    return JSON.parse(JSON.stringify(obj));
}

function genMockUrls() {
    const rulePath = path.join(__dirname, '..', 'deployment', '__tests__', 'resources', 'metadata');
    const [indexStore, indexAggregates] = buildIndexStore(rulePath);
    const searchIndex = buildSearchIndex(indexStore);
    const rootUrl = process.env.PUBLIC_URL;
    let mockUrls = {};
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
    jest.spyOn(global, 'fetch').mockImplementation(fetchMocker.mock);
});

afterEach(() => {
    fetchMocker.reset();
    global.fetch.mockClear();
});

function renderDefaultSearchPage() {
    const history = createMemoryHistory();
    history.push('/rspec/#/rspec/');
    return render(<Router history={history}><SearchPage /></Router>);
}

test('renders the list of all rules', async () => {
    const { findByText, asFragment } = renderDefaultSearchPage();
    await findByText(/rules found/i);
    expect(asFragment()).toMatchSnapshot();
});

test('narrows search by title', async () => {
    const { queryByText, queryByTestId, getByRole } = renderDefaultSearchPage();

    // Finish rendering after fetching all the data
    await waitFor(() => fetchMocker.finished());
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByText(/rules found: 3/i)).not.toBeNull();

    // Enter a search query
    const searchBox = getByRole('textbox');
    fireEvent.change(searchBox, { target: { value: 'should not be used' } });

    expect(queryByTestId('search-hit-S987')).not.toBeNull();
    expect(queryByTestId('search-hit-S1000')).toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();
    expect(queryByText(/rules found: 2/i)).not.toBeNull();
});

test('shows the exact match first', async () => {
    const { queryByText, queryByTestId, getAllByTestId, getByRole } = renderDefaultSearchPage();

    // Finish rendering after fetching all the data
    await waitFor(() => fetchMocker.finished());
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByText(/rules found: 3/i)).not.toBeNull();

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
    const { queryByText, queryByTestId, getByRole, getByTestId } = renderDefaultSearchPage();

    // Finish rendering after fetching all the data
    await waitFor(() => fetchMocker.finished());
    expect(queryByTestId('search-hit-S987')).not.toBeNull();
    expect(queryByText(/rules found: 3/i)).not.toBeNull();

    // Select the rule type
    fireEvent.mouseDown(within(getByTestId('rule-type')).getByRole('button'));
    const listbox = within(getByRole('listbox'));
    fireEvent.click(listbox.getByTestId('rule-type-CODE_SMELL'));

    expect(queryByTestId('search-hit-S987')).toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();
    expect(queryByText(/rules found: 2/i)).not.toBeNull();
});

test('narrows search by rule tags', async () => {
    const { queryByText, queryByTestId, getByRole, getByTestId } = renderDefaultSearchPage();

    // Finish rendering after fetching all the data
    await waitFor(() => fetchMocker.finished());
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByText(/rules found: 3/i)).not.toBeNull();

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
    const { queryByText, queryByTestId, getByRole, getByTestId } = renderDefaultSearchPage();

    // Finish rendering after fetching all the data
    await waitFor(() => fetchMocker.finished());
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByText(/rules found: 3/i)).not.toBeNull();

    // Select the cfamily language, should keep all the rules: they all are specified for cfamily
    fireEvent.mouseDown(within(getByTestId('rule-language')).getByRole('button'));
    const listbox = within(getByRole('listbox'));
    fireEvent.click(listbox.getByTestId('rule-language-cfamily'));
    expect(queryByText(/rules found: 3/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).not.toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();

    // Select the java language: should keep only S3457
    fireEvent.click(listbox.getByTestId('rule-language-java'));
    expect(queryByText(/rules found: 1/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).toBeNull();
    expect(queryByTestId('search-hit-S1000')).toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();
});

test('narrows search by quality profile', async () => {
    const { queryByText, queryByTestId, getByRole, getByTestId } = renderDefaultSearchPage();

    // Finish rendering after fetching all the data
    await waitFor(() => fetchMocker.finished());
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByText(/rules found: 3/i)).not.toBeNull();

    // Select MISRA 2008 recommended and Sonar way profiles - only S1000 and S3457 are in these profiles
    fireEvent.mouseDown(within(getByTestId('rule-default-quality-profile')).getByRole('button'));
    const listbox = within(getByRole('listbox'));
    fireEvent.click(listbox.getByTestId('rule-qual-profile-Sonar way'));
    fireEvent.click(listbox.getByTestId('rule-qual-profile-MISRA C++ 2008 recommended'));
    expect(queryByText(/rules found: 2/i)).not.toBeNull();
    expect(queryByTestId('search-hit-S987')).toBeNull();
    expect(queryByTestId('search-hit-S1000')).not.toBeNull();
    expect(queryByTestId('search-hit-S3457')).not.toBeNull();
});
