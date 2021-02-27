from typing import List, TextIO, Dict

from multiprocessing.pool import ThreadPool

from math import exp

import tqdm

# def map(func, iterable) -> List:
#     return ThreadPool().map(func=func, iterable=iterable)

def getInput(filepath) -> TextIO:
    return open(filepath, "r")

def getOutput(filepath) -> TextIO:
    return open(filepath, "w+")




### Read input ###################################################################
class Street():
    def __init__(self, B, E, name, L) -> None:
        self.beg :int  = B
        self.end :int = E
        self.name :str = name
        self.lgth :int = L
        
        self.cars : List = []
        self.carPassed = False
        # solve info
        self.heuristic_score = -1
        self.gltime = 0
        self.occurences = 0
        
    def __repr__(self) -> str:
        return "Street: {}-->{}".format(self.beg, self.end)


class Car():
    def __init__(self, carId, nbStreets, streets : List[Street]) -> None:
        self.id = carId
        self.nbStreets :int = nbStreets
        self.streets: List[Street] = streets
        self.pos = 0
        self.secLeft = 0
    def __repr__(self) -> str:
        return "Car: streets \n{}".format("\n".join(map(str, self.streets)))

index = int
time = int
class Intersection():
    def __init__(self, iid) -> None:
        # information
        self.iid = iid
        self.ins :  List[Street] = list() # incoming streets
        self.outs:  List[Street] = list() # outgoing streets
        # solution info
        self.order: List[Street] = list() # liste qui donne l'ordre des rues dans le cycle
        self.times: List[time] = list()  
        # compute score info
        self.current_light : index = -1
        self.current_light_time_left : time = -1
        
    @property
    def looptime(self):
        return sum(map(lambda street : street.gltime, self.ins))

    def __repr__(self) -> str:
        return "Intersection: {}".format(self.iid)
    

class Dataset():
    def __init__(self, input_file: TextIO) -> None:
        D, I, S, V, F = map(int, input_file.readline().split(" "))
        # get streets
        self.streets: Dict[str, Street] = dict()
        for _ in range(S):
            B, E, street_name, L = input_file.readline().split(" ")
            B = int(B)
            E = int(E)
            L = int(L)
            self.streets[street_name] = Street(B, E, street_name, L)
        # get cars
        self.cars: List[Car] = []
        for carId in range(V):
            carInfo = input_file.readline().split()
            self.cars.append(Car(carId=carId,
                                 nbStreets=int(carInfo[0]),
                                 streets=list(
                                      map(lambda sName: self.streets[sName], carInfo[1:]))
                                  )
                             )

        self.duration: int = D
        self.nbInt: int = I
        self.bonusPts: int = F
        self.street_amount: int = S

        liste_inter = [self.streets[name].end for name in self.streets]
        nb_inter = max(liste_inter)+1
        
        self.intersections: List[Intersection] = list()
        for i in range(nb_inter):
            self.intersections.append(Intersection(i))
        for street_name in self.streets:
            street = self.streets[street_name]
            self.intersections[street.end].ins.append(street)
            self.intersections[street.beg].outs.append(street)


def proportion_intervalle(a,b, pourcentage):
    return pourcentage * abs(b-a) + min(a,b)


def vertAtTime(t, street : Street, data: Dataset) -> bool:
    """is a given streetlight green at a given time t"""
    endIntersection = data.intersections[street.end]
    street_index = endIntersection.ins.index(street)

    partialIncoming = endIntersection.order[:endIntersection.order.index(street)]
    nbLoop = sum(map(lambda street: street.gltime, partialIncoming))

    if nbLoop < (t % endIntersection.looptime) < nbLoop + endIntersection.ins[street_index].gltime:
        return True
    return False


def score(data: Dataset):
    score = 0
    for t in range(data.duration):
        #reset all streets
        for street_name in data.streets:
            street = data.streets[street_name]
            street.carPassed = False
        #cars
        for car in data.cars:
            if car.pos == car.nbStreets-1 and car.secLeft == 0:
                score += data.bonusPts + (data.duration - t)
            elif car.secLeft != 0:
                #check if space available
                car.secLeft -= 1
            else:
                if (vertAtTime(t, car.streets[car.pos], data) 
                            and car.id == data.streets[car.streets[car.pos].name].cars[0] 
                            and data.streets[car.streets[car.pos].name].carPassed == False):

                    data.streets[car.streets[car.pos].name].cars.pop(0)
                    data.streets[car.streets[car.pos].name].carPassed = True
                    car.pos += 1
                    car.secLeft = data.streets[car.streets[car.pos].name].lgth
                else:
                    data.streets[car.streets[car.pos].name].cars.append(car.id)
    return score

def solve(data : Dataset):
    output = ""
    total_duration = data.duration
    nbIntersect = len(data.intersections)
    output += str(nbIntersect) + "\n"
    
    # etape 1 pondérer les temps
    total_length = 0
    total_cities = 0
    print("step 1")
    for car in tqdm.tqdm(data.cars):
        for street in car.streets:
            street.occurences += 1
            total_length += street.lgth
            total_cities += 1
    for street_name in data.streets:
        street = data.streets[street_name]
        sig = lambda x: 1/(1+ exp(-x/10+5))
        heuristic = street.occurences * street.lgth / (total_length)
        street.gltime = min(total_duration, int(proportion_intervalle(1,total_duration, heuristic)))
    
    # etape 2 ==> calculer ordre en fonction des positions initiales
    print("step 2")
    nbCarsStreet = {streetname : 0 for streetname in data.streets}
    for car in data.cars:
        nbCarsStreet[car.streets[0].name] += 1
    for intersec in tqdm.tqdm(data.intersections):
        streetOrder = []
        for street in intersec.ins:
            streetOrder.append((street, nbCarsStreet[street.name]))    
        streetOrder.sort(key=lambda x:x[1], reverse=True)
        intersec.order = [x[0] for x in streetOrder]
    
    # etape 3 ==> gagner
    print("step 3")
    for intersec in tqdm.tqdm(range(nbIntersect)):
        output += str(intersec) + "\n"
        output += str(len(data.intersections[intersec].ins)) + "\n"
        
        intersection = data.intersections[intersec]
        for street in intersection.order:
            output += " ".join([street.name, str(street.gltime)]) + "\n"
    return output

if __name__ == "__main__":
    filepaths = [[f"./inputs/{chr(97+i)}.txt", f"./outputs/{chr(97+i)}.txt"] for i in range(6)]

    for filepath in range(len(filepaths)):
        print("\n\nfile", chr(97+filepath), "\n")
        lines = getInput(filepaths[filepath][0])
        data = Dataset(lines)
        #print("streets", *map(str, data.streets))
        solution = solve(data)
        test = score(data)
        print(test)
        out_file = getOutput(filepaths[filepath][1])
        out_file.write(solution)
        del data

    

#  fichierOutput = (open("Solution.txt", "w"))
#  output = solve(data)
#  print("helloooo", output)
#  fichierOutput.write(output)

