import { Result, AnalyzeResultDataGraph, AnalyzeResultDataCommonRelation } from '../../types';
import { Graph, GraphConfiguration, GraphData, GraphNode, GraphLink } from 'react-d3-graph';
import { useState } from 'react';
import { Box, Container, List, ListItem, Center, Heading } from '@chakra-ui/react';

const hasRelation = (graph: AnalyzeResultDataGraph, relation: AnalyzeResultDataCommonRelation): boolean => {
  if(!graph || !relation) return false;
  return graph.links.some(l => l.relationship === relation.relationship && l.target === relation.target);
}

export const PlumHoundAnalyzeTask = ({task}: {task: Result<'analyze_path'>}) => {
  const [selectedGraph, setSelectedGraph] = useState(0);
  const [selectedRelation, setSelectedRelation] = useState(-1);

  const getBgColor = (index: number): string => {
    const hasrel = hasRelation(task.results.graphs[index], task.results.mostUsedRelationships[selectedRelation]);
    if(selectedGraph === index){
      if(hasrel) return 'rgba(160,0,0,0.25)';
      else return 'rgba(0,0,0,0.15)';
    }else{
      if(hasrel) return 'rgba(255,0,0,0.2)';
      else return '';
    }
  }

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
          selectedGraph={selectedGraph}
          selectedRelaltion={selectedRelation}
        />
      </Container>

      <Box
        position='absolute'
        top='5px'
        left='5px'
        zIndex='999'
        maxW='380px'
        maxH='765px'
        overflow='auto'
      >
        <Center>
          <Heading size='sm'>Paths</Heading>
        </Center>
        <List>
          {task.results.graphs.map((data, i) => (
            <ListItem
              key={i}
              bg={getBgColor(i)}
              onClick={() => setSelectedGraph(i)}
              cursor='pointer'
              fontSize='80%'
              paddingTop='1px'
              paddingBottom='1px'
              borderBottom='1px dashed lightgrey'
            >
              Path {i + 1} {data.nodes[0].id}
            </ListItem>
          ))}
        </List>
      </Box>

      <Box
        position='absolute'
        top='5px'
        right='5px'
        zIndex='999'
        maxW='300px'
        maxH='765px'
        overflow='auto'
      >
        <Center>
          <Heading size='sm'>Most Used Relationships</Heading>
        </Center>
        <List>
          {task.results.mostUsedRelationships.map((rel, i) => (
            <ListItem
              key={i}
              bg={selectedRelation === i ? 'rgba(0,0,0,0.15)' : ''}
              onClick={() => setSelectedRelation(i)}
              cursor='pointer'
              fontSize='80%'
              paddingTop='1px'
              paddingBottom='1px'
              borderBottom='1px dashed lightgrey'
            >
              {rel.count.toLocaleString()}x {rel.relationship} {rel.target}
            </ListItem>
          ))}
        </List>
      </Box>
    </Box>
  )
}

const PlumHoundGraph = ({
  task,
  selectedGraph,
  selectedRelaltion,
}: {
  task: Result<'analyze_path'>,
  selectedGraph: number,
  selectedRelaltion: number,
}) => {
  const current = task.results.graphs[selectedGraph];
  const currentRelation = task.results.mostUsedRelationships[selectedRelaltion];

  if(!current) return <></>;

  const height = 773;
  const width = 1200;

  const listWidth = 380;

  // values I just felt like looked good.
  const nodeXGap = 64;
  const nodeYGap = 144;

  const data: GraphData<GraphNode, GraphLink> = {
    nodes: current.nodes
      .map((node, i) => ({
        ...node,
        x: i * nodeXGap + listWidth + 10,
        y: i * nodeYGap + 20,
      })),
    links: current.links.map(l => {
      return {
        source: l.source,
        target: l.target,
        label: l.relationship,
        color: (currentRelation && l.target === currentRelation.target && l.relationship === currentRelation.relationship) ? 'red' : undefined,
      }
    }),
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
    width,
    height,
    directed: true,
    d3: {
      disableLinkForce: true,
    } as any, // as any because there is a typing error in the library. this object should be Partial
  };

  // key is used so it remounts the graph instead of just updating its nodes
  // weird split filter nonsense that removes the symbols #, @, or . from the string
  // are because of some weird error thrown when they are included for the id field
  const key = data.nodes[0].id.split('').filter(c => !'#@.'.includes(c)).join('') || task.title;

  return (
    <Graph
      key={key}
      id={key}
      data={data}
      config={myConfig}
    />
  );
}
