import { PlumHoundTable } from '../Table';
import { Result } from '../../types';
import { Center } from '@chakra-ui/react';

export const PlumHoundBusiestTask = ({task}: {task: Result<'busiest_path'>}) => {
  return (
    <Center>
      <PlumHoundTable keys={['name', 'count']} values={task.results} />
    </Center>
  );
}