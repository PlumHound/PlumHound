import { Box, Center, Container, Heading } from '@chakra-ui/react';
import { PlumHoundAnalyzeTask } from './Tasks/AnalyzeTask';
import { PlumHoundBusiestTask } from './Tasks/BusiestTask';
import { PlumHoundQueryTask } from './Tasks/QueryTask';
import { AnyResult, Result } from '../types';

type Props = {
  task: AnyResult | undefined
}
export const PlumHoundTaskContainer = ({ task }: Props) => {
  return (
    <Box
      w='1200px'
      minH='800px'
      rounded='12px'
      boxShadow='sm'
      borderWidth='1px'
      borderColor='gray.900'
      marginLeft='50px'
    >
      <Center borderBottom='1px'>
        <Heading size='md'>{task?.title || 'Select a Task'}</Heading>
      </Center>
      <Container minW='100%' padding='0' margin='0'>
        {(()=>{
          switch(task?.type){
            case 'analyze_path':
              return <PlumHoundAnalyzeTask task={task as Result<'analyze_path'>} />;
            case 'busiest_path':
              return <PlumHoundBusiestTask task={task as Result<'busiest_path'>} />;
            case 'query':
              return <PlumHoundQueryTask task={task as Result<'query'>} />;
            default:
              return '';
          }
        })()}
      </Container>
    </Box>
  )
}