import { ChakraProvider, Flex, ListItem } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { PlumHoundNav } from './components/Nav';
import { PlumHoundList } from './components/List';
import { PlumHoundTaskContainer } from './components/TaskContainer';
import { Report } from './types';



function App() {
  const [results, setResults] = useState<Report | undefined>();
  const [chosenTaskIndex, setChosenTaskIndex] = useState<number>(-1);

  useEffect(() => {
    reloadReports();
  }, []);

  const reloadReports = async () => {
    const ress = await fetch('/api/tasks').then(r => r.json());
    console.log(ress)
    setResults(ress);
    setChosenTaskIndex(0);
  }

  return (
    <ChakraProvider>
      <PlumHoundNav />
      <Flex
        w="100%"
        pt={10}
        justifyContent="center"
        alignItems="center"
      >
        <PlumHoundList heading='Tasks'>
          {
            results && results.tasks ? 
              results.tasks.map((result, i) => {
                return (
                  <ListItem
                    key={i}
                    bg={chosenTaskIndex === i ? 'rgba(0,0,0,0.15)' : ''}
                    onClick={() => setChosenTaskIndex(i)}
                    cursor='pointer'
                    borderBottom='1px'
                    borderColor='lightgray'
                    paddingLeft='5px'
                  >
                    {result.title}
                  </ListItem>
                )
              }) :
              <ListItem
                onClick={reloadReports}
                cursor='pointer'
                borderBottom='1px'
                borderColor='lightgray'
                paddingLeft='5px'
                title='Click reload!'
              >
                No tasks
              </ListItem>
          }
        </PlumHoundList>
        <PlumHoundTaskContainer task={results?.tasks[chosenTaskIndex]} />
      </Flex>
    </ChakraProvider>
  );
}

export default App;
