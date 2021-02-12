import { Result } from '../../types';
import { Graph, GraphConfiguration, GraphData, GraphNode, GraphLink } from 'react-d3-graph';
import { useState } from 'react';
import { Box, Container, List, ListItem } from '@chakra-ui/react';

export const PlumHoundAnalyzeTask = ({task}: {task: Result<'analyze_path'>}) => {
  const [selected, setSelected] = useState(0);
  return (
    <Box
      w='100%'
      position='relative'
    >
      <Container
        position='absolute'
        top='0'
        left='-4'
      >
        <PlumHoundGraph
          task={task}
          index={selected}
        />
      </Container>

      <List
        position='absolute'
        top='3'
        left='3'
        zIndex='999'
        maxH='750px'
        overflow='auto'
      >
        {task.results.map((data, i) => (
          <ListItem
            key={i}
            bg={selected === i ? 'rgba(0,0,0,0.15)' : ''}
            onClick={() => setSelected(i)}
            cursor='pointer'
            fontSize='sm'
          >
            Path {i + 1} {data.nodes[0].id}
          </ListItem>
        ))}
      </List>
    </Box>
  )
}

const PlumHoundGraph = ({task, index}: {task: Result<'analyze_path'>, index: number}) => {
  const current = task.results[index];

  if(!current) return <></>;



  const data: GraphData<GraphNode, GraphLink> = {
    nodes: current.nodes,
    links: current.links
      .filter(l => !current.actionables.some(a => a.a === l.source && a.b === l.target))
      .concat(current.actionables.map(a => ({source:a.a, target:a.b, label: a.rel}))),
  }

  const myConfig: Partial<GraphConfiguration<GraphNode, GraphLink>> = {
    nodeHighlightBehavior: true,
    node: {
      color: "lightgreen",
      size: 120,
      highlightStrokeColor: "blue",
    },
    link: {
      highlightColor: "lightblue",
      renderLabel: true,
    },
    width: 1200,
    height: 773,
    directed: true,
  };

  return (
    <Graph
      id={task.title}
      data={data}
      config={myConfig}
    />
  );
}
