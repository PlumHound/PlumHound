import { ChakraProvider, Flex,  } from "@chakra-ui/react"
import { PlumHoundNav } from './components/nav';

function App() {
  return (
    <ChakraProvider>
      <PlumHoundNav />
      <Flex
        w="100%"
        pt={10}
        justifyContent="center"
        alignItems="center"
      >
        
      </Flex>
    </ChakraProvider>
  );
}

export default App;
