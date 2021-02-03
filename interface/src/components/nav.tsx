import { Flex, Image, Text } from '@chakra-ui/react';
import React from 'react';

export const PlumHoundNav = () => {
  return (
    <Flex
      bg='#A41E63'
      w='100%'
      px={4}
      py={3}
      justifyContent='space-between'
      alignItems="center"
    >
      <Flex flexDirection="row" justifyContent="center" alignItems="center">
        <Image src='logo.png' h={10} rounded='full' /> 
        <Text pl={4} color="white" fontSize='2xl'>PlumHound</Text>
      </Flex>
    </Flex>
  )
}