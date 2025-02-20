
export enum Severity {
    INFO,
    LOW,
    MEDIUM,
    HIGH,
    BLOCKER,
};

export function maxSeverity(impacts: any): Severity {
    let maxSeverity: Severity = Severity.INFO;
    for (const key in impacts) {
        const val = impacts[key];
        const sev: Severity = Severity[val as keyof typeof Severity];
        if (sev > maxSeverity) {
            maxSeverity = sev;
        }
    }
    return maxSeverity;
}

export function compareSeverities(a: string, b:string): number {
    const seva: Severity = Severity[a as keyof typeof Severity];
    const sevb: Severity = Severity[b as keyof typeof Severity];
    return seva - sevb;
}