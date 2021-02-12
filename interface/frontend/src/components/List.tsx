import { Box, Center, Heading, List } from '@chakra-ui/react';
import React from 'react';

type Props = React.PropsWithChildren<{
  heading: string,
}>
export const PlumHoundList = (props: Props) => {
  return (
    <Box
      w='200px'
      h='800px'
      rounded='12px'
      boxShadow='sm'
      borderWidth='1px'
      borderColor='gray.900'
      alignSelf='flex-start'
      >
      <Center borderBottom='1px'>
        <Heading size='md'>{props.heading}</Heading>
      </Center>
      <List>
        {props.children}
      </List>
    </Box>
  )
}