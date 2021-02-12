import { PlumHoundTable } from '../Table';
import { Result } from '../../types';
import { Center } from '@chakra-ui/react';

export const PlumHoundQueryTask = ({task}: {task: Result<'query'>}) => {
  return (
    <Center>
      <PlumHoundTable keys={task.results.keys} values={task.results.result} />
    </Center>
  );
}