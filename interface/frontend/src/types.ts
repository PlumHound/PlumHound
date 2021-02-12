export type ResultType = 'query' | 'analyze_path' | 'busiest_path';

export type Report = {
  name: string,
  format: string,
  path: string,
  tasks: AnyResult[]
}

export type Result<T extends ResultType> = {
  title: string,
  type: T,
  results: {
    query: QueryResultData,
    analyze_path: AnalyzeResultData,
    busiest_path: BusiestResultData,
  }[T]
}

export type AnyResult = Result<ResultType>;

export type QueryResultData = {
  keys: string[],
  result: Record<string, any>[],
}

export type AnalyzeResultData = {
  actionables: {
    a: string,
    b: string,
    rel: string,
  }[],
  nodes: {
    id: string,
  }[],
  links: {
    source: string,
    target: string,
  }[]
}[]

export type BusiestResultData = {
  count: number,
  name: string,
}[];